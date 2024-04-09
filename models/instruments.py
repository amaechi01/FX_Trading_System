# with oandaapi class, i can fetch the tradable instruments for the account id housed in instrument key of the object
# the instrument class here will create an object from the tradable objects returned with only the selected items from objects.

class Instrument:
    def __init__(self, name, ins_type, displayName, pipLocation, tradeUnitsPrecision, marginRate):
        self.name = name
        self.ins_type = ins_type
        self.displayName = displayName
        self.pipLocation = pow(10, pipLocation)
        self.tradeUnitsPrecision = tradeUnitsPrecision
        self.marginRate = float(marginRate)

    def __repr__(self):
        return str(vars(self))
    
    #  the following class medthod will instatiate the Instrument objects using the returned objects from the tradable instruments
    #  associated with the account id.
    @classmethod
    def FromApiObject(cls, ob):
        return Instrument(
            ob['name'],
            ob['type'],
            ob['displayName'],
            ob['pipLocation'],
            ob['tradeUnitsPrecision'],
            ob['marginRate'],
        )
    