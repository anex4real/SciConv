import numpy as np
from scipy.stats import skew, wilcoxon

# NASA TLX Scores
tlx_co = [24.7, 80, 49.3, 56, 78, 39.3, 78, 48, 31.7, 40, 24.7, 56.7, 36, 43, 55, 23.3, 26.7, 33.3, 49.3, 55,32]
tlx_sciconv = [38.3, 35, 32.3, 38.7, 47, 28.7, 28.7, 43, 28.3, 33.7, 35.3, 44.7, 26.7, 36.7, 40.3, 35, 28.7, 41.3, 36.7, 40, 32.3]

# Check for normality using skewness
print("Skewness (NASA TLX - CO):", skew(tlx_co))
print("Skewness (NASA TLX - SciConv):", skew(tlx_sciconv))

# Perform Wilcoxon signed-rank test for NASA TLX scores
tlx_result = wilcoxon(tlx_co, tlx_sciconv)
print("Wilcoxon test result for NASA TLX:", tlx_result)

# SUS Scores
sus_co = [55, 65, 37.5, 50, 30, 57.5, 27.5, 45, 45, 62.5, 75, 47.5, 82.5, 42.5, 85, 50, 62.5, 62.5, 62.5, 27.5,57.5]
sus_sciconv = [85, 90, 75, 82.5, 77.5, 80, 95, 75, 65, 87.5, 97.5, 65, 100, 95, 87.5, 65, 82.5, 100, 87.5, 62.5,87.5]

# Check for normality using skewness
print("Skewness (SUS - CO):", skew(sus_co))
print("Skewness (SUS - SciConv):", skew(sus_sciconv))

# Perform Wilcoxon signed-rank test for SUS scores
sus_result = wilcoxon(sus_co, sus_sciconv)
print("Wilcoxon test result for SUS:", sus_result)
