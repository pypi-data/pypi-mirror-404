import logging
logger = logging.getLogger(__name__)

quantities = {
    'Time': ['s', 'min', 'hr', 'day', 'year', 'yr'],
    'Mass': ['g', 'kg', 't'],
    'Distance': ['um', 'mm', 'cm', 'm', 'km'],
    'Force': ['N', 'kN'],
    'Pressure': ['Pa', 'bar', 'bar(g)', 'bar(a)', 'bar(d)'
                 'mbar', 'mbar(g)', 'mbar(d)', 'mbar(a)',
                 'psi', 'psi(g)', 'psi(d)', 'psi(a)'],
    'Temperature': ['K', 'C', 'degC', 'degK'],
    'Current': ['A', 'mA'],
    'Voltage': ['V', 'mV', 'uV'],
    'Power': ['mW', 'W', 'kW', 'MW'],
    'RPM': ['rpm', 'RPM'],
    'Frequency': ['Hz', 'kHz', 'MHz'],
}

quantities['Massflow'] = [
    "{}/{}".format(m, t)
    for m in quantities['Mass']
    for t in quantities['Time']]

quantities['Velocity'] = [
    "{}/{}".format(d, t)
    for d in quantities['Distance']
    for t in quantities['Time']]

quantities['Acceleration'] = [
    "{}/{}^2".format(d, t)
    for d in quantities['Distance']
    for t in quantities['Time']]

quantities['Moment'] = [
    "{}{}".format(f, d)
    for f in quantities['Force']
    for d in quantities['Distance']]


def quantity_for_unit(unit):
    """
    Return the name of the quantity associated with the given unit.
    """
    matches = [k for k, v in quantities.items() if unit in v]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        logger.warning("Multiple quantities found for unit %s", unit)
        return matches[0]
    else:
        logger.warning("Quantity not found for unit %s", unit)
        return "Unknown"
