% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/prepareMOFA.R
\name{regressCovariates}
\alias{regressCovariates}
\title{regress out a covariate from the training data}
\usage{
regressCovariates(object, views, covariates, min_observations = 5)
}
\arguments{
\item{object}{an untrained \code{\link{MOFAmodel}}}

\item{views}{the view(s) to regress out the covariates.}

\item{covariates}{a vector (one covariate) or a data.frame (for multiple covariates) where each row corresponds to one sample, sorted in the same order as in the input data matrices. 
You can check the order by doing sampleNames(MOFAobject). If required, fill missing values with \code{NA}, which will be ignored when fitting the linear model.}

\item{min_observations}{number of non-missing observations required}
}
\value{
Returns an untrained \code{\link{MOFAmodel}} where the specified covariates have been regressed out in the training data.
}
\description{
Function to regress out a covariate from the training data.\cr
If you have technical sources of variability (i.e. batch effects) that you do not want to be captured by factors in the model, 
you should regress them out before fitting MOFA. This function performs a simple linear regression model, extracts the residuals,
and replaces the original data in the TrainingData slot. \cr
Why is this important? If big technical factors exist, the model will "focus" on capturing the variability driven by these factors, and smaller sources of variability could be missed. \cr
But... can we not simply add those covariates to the model? Technically yes, but we extensively tested this functionality and it was not yielding good results. \cr 
The reason is that covariates are usually discrete labels that do not reflect the underlying molecular biology. 
For example, if you introduce age as a covariate, but the actual age is different from the "molecular age", 
the model will simply learn a new factor that corresponds to this "latent" molecular age, and it will drop the covariate from the model.\cr
We recommend factors to be learnt in a completely unsupervised manner and subsequently relate them to the covariates via visualisation or via a simple correlation analysis (see our vignettes for more details).
}
