import numpy as np
from scipy.stats import gamma
from scipy.special import gammainc
from scipy.optimize import root

class TruncatedGamma:
    """Class object for the truncated gamma distribution.
    
    This class object calculates distribution parameters for a truncated gamma distribution.
    
    Attributes:
        A (int or float): The lower bound for the truncated gamma distribution.
        B (int or float): The upper bound for the truncated gamma distribution.
        alpha (int or float): The value of the parameter alpha.
        theta (int or float): The value of the parameter theta.
    """
    
    def __init__(self, A, B, alpha, theta):
        """Initializes a new TruncatedGamma instance.
        
        Args:
            A (int or float): The lower bound for the truncated gamma distribution.
            B (int or float): The upper bound for the truncated gamma distribution.
            alpha (int or float): The value of the parameter alpha.
            theta (int or float): The value of the parameter theta.
        
        Attributes:
            A (int or float): The lower bound for the truncated gamma distribution.
            B (int or float): The upper bound for the truncated gamma distribution.
            alpha (int or float): The value of the parameter alpha.
            theta (int or float): The value of the parameter theta.
        
        Returns:
            None
        
        Raises:
            ValueError if alpha is less than zero.
            ValueError if theta is less than zero.
            ValueError if A is less than zero.
            ValueError if B is less than or equal to A.
        
        Example:
            x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
            x.alpha, x.theta, x.A, x.B
        """
        
        if alpha <= 0:
            raise ValueError("The value of alpha should be greater than zero.")
        
        if theta <= 0:
            raise ValueError("The value of theta should be greater than zero.")
        
        if A < 0:
            raise ValueError("The lower bound A should be greater than or equal to zero.")
        
        if B <= A:
            raise ValueError("The upper bound B should be greater than A.")
        
        self.alpha = alpha
        self.theta = theta
        self.A = A
        self.B = B
        
        return None
    
    def truncgamma_m1(self):
        """
        Calculate the first moment for the truncated gamma distribution.
        
        Args:
            None
        
        Attributes:
            None
        
        Returns:
            Returns the first moment of the truncated gamma distribution.
        
        Example:
            >>> x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
            >>> x.truncgamma_m1()
        """
        zA, zB = self.A/self.theta, self.B/self.theta
        denominator = gammainc(self.alpha, zB) - gammainc(self.alpha, zA)
        numerator = gammainc(self.alpha + 1, zB) - gammainc(self.alpha + 1, zA)
        m1 = self.alpha*self.theta*(numerator/denominator)
        return m1
    
    def truncgamma_m2(self):
        """
        Calculate the second moment for the truncated gamma distribution.
        
        Args:
            None
        
        Attributes:
            None
        
        Returns:
            Returns the second moment of the truncated gamma distribution.
        
        Example:
            >>> x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
            >>> x.truncgamma_m2()
        """
        zA, zB = self.A/self.theta, self.B/self.theta
        denominator = gammainc(self.alpha, zB) - gammainc(self.alpha, zA)
        numerator = gammainc(self.alpha + 2, zB) - gammainc(self.alpha + 2, zA)
        m2 = self.alpha*(self.alpha + 1)*self.theta**2*(numerator/denominator)
        return m2
    
    def truncgamma_var(self):
        """
        Calculate the variance for the truncated gamma distribution.
        
        Args:
            None
        
        Attributes:
            None
        
        Returns:
            Returns the variance of the truncated gamma distribution.
        
        Example:
            >>> x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
            >>> x.truncgamma_var()
        """
        m1 = self.truncgamma_m1()
        m2 = self.truncgamma_m2()
        variance = m2 - m1**2
        return variance
    
    def truncgamma_cv(self):
        """
        Calculate the coefficient of variation for the truncated gamma distribution.
        
        Args:
            None
        
        Attributes:
            None
        
        Returns:
            Returns the coefficient of variation of the truncated gamma distribution.
        
        Example:
            >>> x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
            >>> x.truncgamma_cv()
        """
        var = self.truncgamma_var()
        mean = self.truncgamma_m1()
        cv = var**0.5/mean
        return cv

def truncgamma_rvs(mean_target, cv_target, A, B, size = 1, random_state = None):
    """
    Generate random variates from a truncated gamma distribution.
    
    Args:
        mean_target (int or float):  The target mean for truncated gamma distribution.
        cv_target (float):  The target coefficient of variation for truncated gamma distribution.
        A (int or float): The lower bound for the truncated gamma distribution.
        B (int or float): The upper bound for the truncated gamma distribution.
        size (int): The number of random variates to generate.
        random_state (int): The seed for random number generation to create reproducible results.
     
    Returns:
        A numpy.ndarray containing the random variates from a truncated gamma distribution.
    
    Example:
        >>> x = truncgamma_rvs(mean_target = 100, cv_target = 1/2, A = 0, B = 1000, size = 10, random_state = 123)
    """
    # Calculate the starting values of alpha and theta from an untruncated gamma distribution
    alpha0 = 1/cv_target**2
    theta0 = mean_target/alpha0
    
    # Find the roots from the first and second moments of the truncated gamma distrubtion to determine the values of alpha theta for the target mean and coefficient of variation.
    def system(vars):
        log_alpha, log_theta = vars
        alpha, theta = np.exp(log_alpha), np.exp(log_theta)
        x = TruncatedGamma(alpha = alpha, theta = theta, A = A, B = B)
        mean = x.truncgamma_m1()
        cv = x.truncgamma_cv()
        return np.array([mean - mean_target, cv - cv_target])
    
    x0 = np.array([np.log(alpha0), np.log(theta0)])
    sol = root(system, x0, method='hybr')
    
    if not sol.success: 
        raise ValueError(f"Unable to find alpha and theta using the 2D-solver!:\n\n{sol}")
    else:
        alpha, theta = np.exp(sol.x)
    
    # Use the calculated values of alpha and theta to draw samples from the truncated gamma distrubtion.
    rng = np.random.default_rng(random_state)
    FA = gamma.cdf(x = A, a = alpha, scale = theta)
    FB = gamma.cdf(x = B, a = alpha, scale = theta)
    u = rng.uniform(FA, FB, size = size)
    res = gamma.ppf(u, a = alpha, scale = theta)
    
    return res