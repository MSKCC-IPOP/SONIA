#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 15:12:15 2019

@author: administrator
"""

import numpy as np
import os

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

#Load OLGA for seq generation
import olga.load_model as load_model
from QmodelCDR3 import QmodelCDR3
from utils_parallel import compute_all_pgens


class QmodelCDR3_LPosLenAA(QmodelCDR3):

    def __init__(self, features = [], constant_features = [], data_seqs = [], gen_seqs = [], chain_type = 'humanTRB', load_model = None, include_genes = True, processes = None):

        QmodelCDR3.__init__(self, features, constant_features, data_seqs, gen_seqs, chain_type, load_model, processes)

        if load_model is None:
            self.min_L = min([len(x[0]) for x in (gen_seqs + data_seqs)])
            self.max_L = max([len(x[0]) for x in (gen_seqs + data_seqs)])
            self.add_features(include_genes, add_data_seqs = data_seqs, add_gen_seqs = gen_seqs) #sequences are only added along with features so update_model doesn't need to be called twice
        else:
            self.min_L = min([len(x[0]) for x in (self.gen_seqs + self.data_seqs)])
            self.max_L = max([len(x[0]) for x in (self.gen_seqs + self.data_seqs)])
            self.amino_acids =  'ARNDCQEGHILKMFPSTWYV'


    def add_features(self, min_L = None, max_L = None, include_genes = True,add_data_seqs=[],add_gen_seqs=[]):
        """Generates a list of feature_strs for a model that parametrize every amino acid
        by the CDR3 length and position from the left (Cys)


        Parameters
        ----------
        min_L : int
            Minimum length CDR3 sequence
        max_L : int
            Maximum length CDR3 sequence
        include_genes : bool
            If true, features for gene selection are also generated

        """

        if min_L == None:
            min_L = self.min_L
        if max_L == None:
            max_L = self.max_L

        self.amino_acids =  'ARNDCQEGHILKMFPSTWYV'
        features = []
        L_features = [['l' + str(L)] for L in range(min_L, max_L + 1)]
        features += L_features
        for L in range(min_L, max_L + 1):
            for i in range(L):
                for aa in self.amino_acids:
                     features.append(['l' + str(L), 'a' + aa + str(i)])

        if include_genes:
            main_folder = os.path.join(os.path.dirname(load_model.__file__), 'default_models', self.chain_type)

            params_file_name = os.path.join(main_folder,'model_params.txt')
            V_anchor_pos_file = os.path.join(main_folder,'V_gene_CDR3_anchors.csv')
            J_anchor_pos_file = os.path.join(main_folder,'J_gene_CDR3_anchors.csv')

            genomic_data = load_model.GenomicDataVDJ()
            genomic_data.load_igor_genomic_data(params_file_name, V_anchor_pos_file, J_anchor_pos_file)

            features += [[v, j] for v in set(['v' + genV[0].split('*')[0].split('V')[-1] for genV in genomic_data.genV]) for j in set(['j' + genJ[0].split('*')[0].split('J')[-1] for genJ in genomic_data.genJ])]

        self.update_model(add_features=features, add_constant_features=L_features, add_data_seqs = add_data_seqs, add_gen_seqs = add_gen_seqs) #adds featires and compute them for the sequences

        self.feature_dict = {tuple(x):i for i,x in enumerate(self.features)}

    def set_gauge(self, min_L = None, max_L = None):
        """ multiply all paramaters of the same position and length (all amino acids) by a common factor
        so sum_aa(gen_marginal(aa) * model_paramaters(aa)) = 1


        Parameters
        ----------
        min_L : int
            Minimum length CDR3 sequence, if not given taken from class attribute
        max_L : int
            Maximum length CDR3 sequence, if not given taken from class attribute

        """
        if min_L == None:
            min_L = self.min_L
        if max_L == None:
            max_L = self.max_L

        #min_L = min([int(x.split('_')[0][1:]) for x in self.features if x[0]=='L'])
        #max_L = max([int(x.split('_')[0][1:]) for x in self.features if x[0]=='L'])

        for l in range(min_L, max_L + 1):
            if self.gen_marginals[self.feature_dict[('l' + str(l),)]]>0:
                for i in range(l):
                    G = sum([self.gen_marginals[self.feature_dict[('l' + str(l), 'a' + aa + str(i))]]
                                    /self.gen_marginals[self.feature_dict[('l' + str(l),)]] *
                                    np.exp(self.model_params[self.feature_dict[('l' + str(l), 'a' + aa + str(i))]])
                                    for aa in self.amino_acids])
                    for aa in self.amino_acids:
                        self.model_params[self.feature_dict[('l' + str(l), 'a' + aa + str(i))]] -= np.log(G)

    def plot_onepoint_values(self, onepoint = None ,onepoint_dict = None,  min_L = None, max_L = None, min_val = None, max_value = None,
                             title = '', cmap = 'seismic', bad_color = 'black', aa_color = 'white', marginals = False):
        """ plot a function of aa, length and position from left, one heatplot per aa


        Parameters
        ----------
        onepoint : ndarray
            array containting one-point values to plot, in the same shape as self.features,
            expected unless onepoint_dict is given
        onepoint_dict : dict
            dict of the one-point values to plot, keyed by the feature tuples such as (l12,aA8)
        min_L : int
            Minimum length CDR3 sequence
        max_L : int
            Maximum length CDR3 sequence
        min_val : float
            minimum value to plot
        max_val : float
            maximum value to plot
        title : string
            title of plot to display
        cmap : colormap
            colormap to use for the heatplots
        bad_color : string
            color to use for nan values - used primarly for cells where position is larger than length
        aa_color : string
            color to use for amino acid names for each heatplot displayed on the bad_color background
        marginals : bool
            if true, indicates marginals are to be plotted and this sets cmap, bad_color and aa_color

        """

        from mpl_toolkits.axes_grid1 import AxesGrid

        if marginals: #style for plotting marginals
            cmap = 'plasma'
            bad_color = 'white'
            aa_color = 'black'

        amino_acids_dict = {'A': 'Ala', 'R': 'Arg', 'N': 'Asn', 'D': 'Asp', 'C': 'Cys', 'E': 'Glu', 'Q': 'Gln', 'G': 'Gly', 'H': 'His', 'I': 'Ile',
                       'L': 'Leu', 'K': 'Lys', 'M': 'Met', 'F': 'Phe', 'P': 'Pro', 'S': 'Ser', 'T': 'Thr', 'W': 'Trp', 'Y': 'Tyr', 'V': 'Val'}

        fig = plt.figure(figsize=(12, 8))

        grid = AxesGrid(fig, 111,
                    nrows_ncols=(4, 5),
                    axes_pad=0.05,
                    cbar_mode='single',
                    cbar_location='right',
                    cbar_pad=0.1,
                    share_all = True
                    )

        current_cmap = matplotlib.cm.get_cmap(name = cmap)
        current_cmap.set_bad(color = bad_color)
        current_cmap.set_under(color = 'gray')

        for a,aa in enumerate(self.amino_acids):

            M = np.empty((max_L - min_L + 1, max_L))
            M[:] = np.nan

            for l in range(min_L, max_L + 1):
                for i in range(l):
                    if onepoint_dict == None:
                        M[l-min_L,i] = onepoint[self.feature_dict[('l' + str(l), 'a' + aa + str(i))]]
                    else:
                        M[l-min_L,i] = onepoint_dict.get(('l' + str(l), 'a' + aa + str(i)), np.nan)

            im = grid[a].imshow(M, cmap = current_cmap, vmin = min_val, vmax = max_value)
            grid[a].text(0.75,0.7,amino_acids_dict[aa],transform=grid[a].transAxes, color = aa_color, fontsize = 'large', fontweight = 'bold')

        grid.cbar_axes[0].colorbar(im)



        grid.axes_llc.set_xticks(range(0, max_L, 2))
        grid.axes_llc.set_xticklabels(range(1, max_L + 1, 2))
        grid.axes_llc.set_yticks(range(0, max_L - min_L + 1 ))
        grid.axes_llc.set_yticklabels(range(min_L, max_L + 1))

        fig.suptitle(title, fontsize=20.00)

    def plot_model_parameters(self, low_freq_mask = 0.0):
        """ plot the model parameters using plot_onepoint_values

        Parameters
        ----------
        low_freq_mask : float
            threshold on the marginals, anything lower would be grayed out

        """
        p1 = np.exp(-self.model_params)
        if low_freq_mask:
            p1[(self.data_marginals < low_freq_mask) & (self.gen_marginals < low_freq_mask)] = -1
        self.plot_onepoint_values(onepoint = p1, min_L = 8, max_L = 16, min_val = 0, max_value = 2, title = 'model parameters q=exp(-E)')

    def norm_marginals(self, marg, min_L = None, max_L = None):
        """ renormalizing the marginals accourding to length, so the sum of the marginals over all amino acid
            for one position/length combination will be 1 (and not the fraction of CDR3s of this length)

        Parameters
        ----------
        marg : ndarray
            the marginal to renormalize
        min_L : int
            Minimum length CDR3 sequence, if not given taken from class attribute
        max_L : int
            Maximum length CDR3 sequence, if not given taken from class attribute


        """

        if min_L == None:
            min_L = self.min_L
        if max_L == None:
            max_L = self.max_L

        for l in range(min_L, max_L + 1):
            for i in range(l):
                for aa in self.amino_acids:
                    if marg[self.feature_dict[('l' + str(l),)]]>0:
                        marg[self.feature_dict[('l' + str(l), 'a' + aa + str(i))]] /= marg[self.feature_dict[('l' + str(l),)]]
        #length_correction = np.array([(marg[self.feature_dict[f.split('_')[0]]] if ('_' in f) else 1.0) for f in self.features])
        #length_correction[length_correction == 0] = 1 #avoid dividing by zero if there is no seq of this length
        return marg


    def plot_marginals_length_corrected(self, min_L = 8, max_L = 16, log_scale = True):

        """ plot length normalized marginals using plot_onepoint_values

        Parameters
        ----------
        min_L : int
            Minimum length CDR3 sequence, if not given taken from class attribute
        max_L : int
            Maximum length CDR3 sequence, if not given taken from class attribute
        log_scale : bool
            if True (default) plots marginals on a log scale
        """

        if log_scale:
            pc = 1e-10 #pseudo count to add to marginals to avoid log of zero
            self.plot_onepoint_values(onepoint = np.log(self.norm_marginals(self.data_marginals) + pc), min_L=min_L, max_L=max_L ,
                                      min_val = -8, max_value = 0, title = 'log(data marginals)', marginals = True)
            self.plot_onepoint_values(onepoint = np.log(self.norm_marginals(self.gen_marginals) + pc), min_L=min_L, max_L=max_L,
                                      min_val = -8, max_value = 0, title = 'log(generated marginals)', marginals = True)
            self.plot_onepoint_values(onepoint = np.log(self.norm_marginals(self.model_marginals) + pc), min_L=min_L, max_L=max_L,
                                      min_val = -8, max_value = 0, title = 'log(model marginals)', marginals = True)
        else:
            self.plot_onepoint_values(onepoint = self.norm_marginals(self.data_marginals), min_L=min_L, max_L=max_L,
                                      min_val = 0, max_value = 1, title = 'data marginals', marginals = True)
            self.plot_onepoint_values(onepoint = self.norm_marginals(self.gen_marginals), min_L=min_L, max_L=max_L,
                                      min_val = 0, max_value = 1, title = 'generated marginals', marginals = True)
            self.plot_onepoint_values(onepoint = self.norm_marginals(self.model_marginals), min_L=min_L, max_L=max_L,
                                      min_val = -8, max_value = 0, title = 'model marginals', marginals = True)


    def compute_energies(self):
        '''
        Compute energies for all sequences
        '''

        self.set_gauge() # set gauge for proper energies
        self.energies_data = np.zeros(len(self.data_seq_features))

        for i, seq_features in enumerate(self.data_seq_features):
                    self.energies_data[i] = self.compute_seq_energy(seq_features = seq_features)

        self.energies_gen = np.zeros(len(self.gen_seq_features))
        for i, seq_features in enumerate(self.gen_seq_features):
                    self.energies_gen[i] = self.compute_seq_energy(seq_features = seq_features)

    def rejection_vector(self,upper_bound=10):
        '''
        Compute rejection

        Parameters
        ----------
        upper_bound : int or float
        accept all above the threshold (domain of validity of the model)

        '''

        self.compute_energies()

        # sample from uniform distribution
        random_samples=np.random.uniform(size=len(self.gen_seqs))
        self.Q_gen=np.exp(-self.energies_gen)
        self.Z=np.sum(self.Q_gen)/len(self.Q_gen)

        #rejection vector
        self.rejection_selection=random_samples < np.clip(self.Q_gen/self.Z,0,upper_bound)/float(upper_bound)

        print 'acceptance frequency:',np.sum(self.rejection_selection)/float(len(self.rejection_selection))

    def compute_pgen(self,rejection_bound=10):
        '''
        Compute pgen for all seqs in the dataset in parallel

        TODO: enrich with new generated sequences because rejection vector reduces the number of generated sequences
        nb:You can enrich and reject before computing pgen (which is the step that takes longer)

        TODO: at the moment works only with IncludeGenes=True option.
        I haven't worked on the other, but minor changes are required (call different olga function in compute_all_pgens)
        '''
        # compute pgens if they do not exist
        try: self.pgen_data
        except: self.pgen_data=compute_all_pgens(self.data_seqs,self.chain_type,self.processes) # multiprocessor version
        try: self.pgen_gen
        except: self.pgen_gen=compute_all_pgens(self.gen_seqs,self.chain_type,self.processes) # multiprocessor version

        self.compute_energies()
        self.rejection_vector(rejection_bound)
        self.pgen_model=np.array(self.pgen_gen)[self.rejection_selection] #add energies

    def compute_ppost(self):
        '''
        Compute ppost by weighting with selection factor Q=exp(-E)
        '''
        self.compute_energies()
        self.ppost_data=self.pgen_data*np.exp(-self.energies_data)
        self.ppost_gen=self.pgen_gen*np.exp(-self.energies_gen)
        self.ppost_model=self.pgen_model*np.exp(-self.energies_gen)[self.rejection_selection] #add energies


    def plot_pgen(self,n_bins=100):
        '''
        Histogram plot of Pgen
        '''
        plt.figure(figsize=(12,8))
        binning_=np.linspace(-20,-5,n_bins)

        plt.hist(np.nan_to_num(np.log10(self.pgen_data)),binning_,histtype='step',normed=True,label='data')
        plt.hist(np.nan_to_num(np.log10(self.pgen_gen)),binning_,histtype='step',normed=True,label='pre-sel')
        plt.hist(np.nan_to_num(np.log10(self.pgen_model)),binning_,histtype='step',normed=True,label='post-sel')

        plt.xlabel('$log_{10} P_{pre}$',fontsize=20)
        plt.ylabel('density',fontsize=20)
        plt.legend()
        plt.show()

    def plot_ppost(self,n_bins=100):
        '''
        Histogram plot of Ppost
        '''
        plt.figure(figsize=(12,8))
        binning_=np.linspace(-20,-5,n_bins)

        plt.hist(np.nan_to_num(np.log10(self.ppost_data)),binning_,histtype='step',normed=True,label='data')
        plt.hist(np.nan_to_num(np.log10(self.ppost_gen)),binning_,histtype='step',normed=True,label='pre-sel')
        plt.hist(np.nan_to_num(np.log10(self.ppost_model)),binning_,histtype='step',normed=True,label='post-sel')

        plt.xlabel('$log_{10} P_{post}$',fontsize=20)
        plt.ylabel('density',fontsize=20)
        plt.legend()
        plt.show()

    def compute_vj_features(self):
        '''
        Compute vj features, useful for plotting (see next function)
        '''
        main_folder = os.path.join(os.path.dirname(load_model.__file__), 'default_models', self.chain_type)
        params_file_name = os.path.join(main_folder,'model_params.txt')
        V_anchor_pos_file = os.path.join(main_folder,'V_gene_CDR3_anchors.csv')
        J_anchor_pos_file = os.path.join(main_folder,'J_gene_CDR3_anchors.csv')

        genomic_data = load_model.GenomicDataVDJ()
        genomic_data.load_igor_genomic_data(params_file_name, V_anchor_pos_file, J_anchor_pos_file)
        self.vj_features=[[v, j] for v in set(['v' + genV[0].split('*')[0].split('V')[-1] for genV in genomic_data.genV]) for j in set(['j' + genJ[0].split('*')[0].split('J')[-1] for genJ in genomic_data.genJ])]

    def plot_marginals_vjl(self):

        '''
        Plot marginals P(L), P(Jgene),P(Vgene)
        '''

        self.compute_vj_features()
        l_unique=np.unique(np.array([['l' + str(L)] for L in range(self.min_L, self.max_L + 1)]))
        v_unique=np.unique(np.array(self.vj_features)[:,0])
        j_unique=np.unique(np.array(self.vj_features)[:,1])

        def l_marginal(type_='model'):
            index=np.array(['model','data','gen'])
            functions= np.array([self.model_marginals,self.data_marginals,self.gen_marginals])

            l_vec=np.zeros(len(l_unique))
            for i_,i in enumerate(l_unique):
                l_vec[i_]=functions[index==type_][0][self.feature_dict[(i,)]]
            return l_vec

        def vj_matrix(type_='model'):
            index=np.array(['model','data','gen'])
            functions= np.array([self.model_marginals,self.data_marginals,self.gen_marginals])

            M=np.zeros((len(v_unique),len(j_unique)))
            for i_,i in enumerate(v_unique):
                for j_,j in enumerate(j_unique):
                    M[i_,j_]= functions[index==type_][0][self.feature_dict[(i,j)]]
            return M

        #plot
        plt.figure(figsize=(16,4))
        plt.subplot(121)
        plt.title('Marginal P(L)')
        l=np.array([i[1:] for i in l_unique],dtype=np.int)
        sort=np.argsort(l)[::-1]
        for i in ['model','data','gen']:
            plt.plot(l[sort],l_marginal(i)[sort],label=i)
        plt.legend()
        plt.subplot(122)

        plt.title('Marginal P(J)')
        values=vj_matrix('data').sum(axis=0)
        sort=np.argsort(values)[::-1]

        for i in ['model','data','gen']:
            plt.scatter(j_unique[sort],vj_matrix(i).sum(axis=0)[sort],label=i)
        plt.xticks(rotation='vertical')
        plt.legend()


        plt.figure(figsize=(16,4))
        plt.title('Marginal P(V)')
        values=vj_matrix('data').sum(axis=1)
        sort=np.argsort(values)[::-1]
        for i in ['model','data','gen']:
            plt.scatter(v_unique[sort],vj_matrix(i).sum(axis=1)[sort],label=i)
        plt.xticks(rotation='vertical')
        plt.legend()
        plt.show()
