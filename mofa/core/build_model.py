"""
Module with functions to build the model
"""

import scipy as s
from sys import path
from time import time,sleep
import pandas as pd
import numpy as np
#from joblib import Parallel, delayed

from .init_nodes import *
from .BayesNet import BayesNet
from .utils import *

def runMOFA(data, data_opts, model_opts, train_opts, seed=None):
    """Method to run a MOFA model
    data: 
    data_opts
    model_opts:
    train_opts:
    seed:

    PARAMETERS
    ----------
    """

    # set the seed
    if seed is None or seed==0:
        seed = int(round(time()*1000)%1e6)
    s.random.seed(seed)


    ###########################
    ## Perform sanity checks ##
    ###########################

    # Create output directory
    if not os.path.isdir(os.path.dirname(data_opts["outfile"])):
        print("Output directory does not exist, creating it...")
        os.makedirs(os.path.dirname(data_opts["outfile"]))

    ####################
    ## Parse the data ##
    ####################

    # Mask
    if 'maskAtRandom' in data_opts or 'maskNSamples' in data_opts:
        if any(data_opts['maskAtRandom']) or any(data_opts['maskNSamples']):
            data = maskData(data, data_opts)

    ######################
    ## Define the model ##
    ######################

    print ("\n")
    print ("#"*24)
    print ("## Building the model ##")
    print ("#"*24)
    print ("\n")
    sleep(1)

    print("Setting random seed %i...\n" % seed)

    # Define dimensionalities
    M = len(data)
    N = data[0].shape[0]
    D = s.asarray([ data[m].shape[1] for m in range(M) ])
    K = model_opts["factors"]
    dim = {'M':M, 'N':N, 'D':D, 'K':K }

    ## Define and initialise the nodes ##

    init = initModel(dim, data, model_opts["likelihoods"], seed=seed)

    # Latent variables
    init.initZ(pmean=model_opts["priorZ"]["mean"], pvar=model_opts["priorZ"]["var"],
               qmean=model_opts["initZ"]["mean"], qvar=model_opts["initZ"]["var"], qE=model_opts["initZ"]["E"], qE2=model_opts["initZ"]["E2"],
               covariates=data_opts['covariates'], scale_covariates=data_opts['scale_covariates'])

    # Sparse weights
    init.initSW(ptheta=model_opts["priorSW"]["Theta"], pmean_S0=model_opts["priorSW"]["mean_S0"], pvar_S0=model_opts["priorSW"]["var_S0"], pmean_S1=model_opts["priorSW"]["mean_S1"], pvar_S1=model_opts["priorSW"]["var_S1"],
                qtheta=model_opts["initSW"]["Theta"], qmean_S0=model_opts["initSW"]["mean_S0"], qvar_S0=model_opts["initSW"]["var_S0"], qmean_S1=model_opts["initSW"]["mean_S1"], qvar_S1=model_opts["initSW"]["var_S1"],
                qEW_S0=model_opts["initSW"]["EW_S0"], qEW_S1=model_opts["initSW"]["EW_S1"], qES=model_opts["initSW"]["ES"])

    # ARD on weights
    init.initAlphaW_mk(pa=model_opts["priorAlphaW"]['a'], pb=model_opts["priorAlphaW"]['b'],
                       qa=model_opts["initAlphaW"]['a'], qb=model_opts["initAlphaW"]['b'], qE=model_opts["initAlphaW"]['E'])

    # Precision of noise
    init.initTau(pa=model_opts["priorTau"]['a'], pb=model_opts["priorTau"]['b'],
                 qa=model_opts["initTau"]['a'], qb=model_opts["initTau"]['b'], qE=model_opts["initTau"]['E'])

    # Sparsity on the weights
    if len(s.unique(model_opts['sparsity'])) == 1:

        # All are infered
        if s.unique(model_opts['sparsity'])==1.:
            # init.initThetaLearn(pa=model_opts["priorTheta"]['a'], pb=model_opts["priorTheta"]['b'],
            #     qa=model_opts["initTheta"]['a'],  qb=model_opts["initTheta"]['b'], qE=model_opts["initTheta"]['E'])
            init.initThetaMixed(pa=model_opts["priorTheta"]['a'], pb=model_opts["priorTheta"]['b'],
                qa=model_opts["initTheta"]['a'],  qb=model_opts["initTheta"]['b'], qE=model_opts["initTheta"]['E'],
                sparsity=model_opts['sparsity'])

        # None are infered
        elif s.unique(model_opts['sparsity'])==0.:
            init.initThetaConst(value=model_opts["initTheta"]['E'])

    # Some are infered
    else:
        init.initThetaMixed(pa=model_opts["priorTheta"]['a'], pb=model_opts["priorTheta"]['b'],
            qa=model_opts["initTheta"]['a'],  qb=model_opts["initTheta"]['b'], qE=model_opts["initTheta"]['E'],
            sparsity=model_opts['sparsity'])

    # Observed data
    init.initY()

    # Define the markov blanket of each node
    nodes = init.getNodes()
    nodes["Z"].addMarkovBlanket(SW=nodes["SW"], Tau=nodes["Tau"], Y=nodes["Y"])
    nodes["Theta"].addMarkovBlanket(SW=nodes["SW"])
    nodes["AlphaW"].addMarkovBlanket(SW=nodes["SW"])
    nodes["SW"].addMarkovBlanket(Z=nodes["Z"], Tau=nodes["Tau"], Alpha=nodes["AlphaW"], Y=nodes["Y"], Theta=nodes["Theta"])
    nodes["Y"].addMarkovBlanket(Z=nodes["Z"], SW=nodes["SW"], Tau=nodes["Tau"])
    nodes["Tau"].addMarkovBlanket(Z=nodes["Z"], SW=nodes["SW"], Y=nodes["Y"])

    ##################################
    ## Add the nodes to the network ##
    ##################################

    # Initialise Bayesian Network
    net = BayesNet(dim=dim, schedule=model_opts["schedule"], nodes=init.getNodes(), options=train_opts)

    ####################
    ## Start training ##
    ####################

    print ("\n")
    print ("#"*45)
    print ("## Running MOFA with seed %d ##" % seed)
    print ("#"*45)
    print ("\n")
    sleep(1)
    
    net.iterate()

    ####################
    ## Save model ##
    ####################

    print("\n")
    print("#"*43)
    print("## Training finished, processing results ##")
    print("#"*43)
    print("\n")


    ##################
    ## Save results ##
    ##################
    
    sample_names = data[0].index.tolist()
    feature_names = [  data[m].columns.values.tolist() for m in range(len(data)) ]
    print("Saving model in %s...\n" % data_opts['outfile'])
    saveModel(net, outfile=data_opts['outfile'], 
        view_names=data_opts['view_names'], sample_names=sample_names, feature_names=feature_names,
        train_opts=train_opts, model_opts=model_opts)