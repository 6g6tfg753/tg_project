def get_ll_spn(toponym):
    ll = list(map(lambda x: str(x), toponym["Point"]["pos"].split()))
    lowercorner = list(map(lambda x: float(x), toponym["boundedBy"]["Envelope"]["lowerCorner"].split()))
    uppercorner = list(map(lambda x: float(x), toponym["boundedBy"]["Envelope"]["upperCorner"].split()))
    spn = list(map(lambda x: str(x), [uppercorner[0] - lowercorner[0], uppercorner[1] - lowercorner[1]]))
    return ll, spn
