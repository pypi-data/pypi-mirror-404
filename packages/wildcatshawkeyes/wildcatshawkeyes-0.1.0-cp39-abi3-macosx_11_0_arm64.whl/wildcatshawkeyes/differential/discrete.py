def diff(t, x):
    """
    Compute the discrete derivative of a timeseries.
    
    Parameters:
        t: Python list of time values
        x: Python list of signal values
    
    Returns:
        Python list containing the discrete derivative v(t)
    """
    # Check for equality of lengths
    if len(t) != len(x):
        raise ValueError("Time and signal arrays must have equal length")
    
    # Initialize the output array
    v = []
    
    # Compute discrete derivative: v(t) = (x(t) - x(t-1)) / (t - t-1)
    for k in range(1, len(t)):
        derivative = (x[k] - x[k-1]) / (t[k] - t[k-1])  # discrete derivative formula
        v.append(derivative)
    
    return v
