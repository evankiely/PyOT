import Adafruit_DHT, math, time


# Defining Sensor class that will be used to hold values specific to a given sensor and location
class Sensor:
    # Defining initialization requirements and their corresponding methods
    def __init__(self, pin, sensor, location):
        self.pin = pin
        self.count = 0
        self.type = sensor
        self.location = location


class Thermometer:
    def __init__(self, sensor):
        self.sensor = sensor

    def increment_count(self):
        self.sensor.count += 1

    # TODO: add breaking condition that also notifies user of potentially faulty sensor
    def get_rh_and_temp(self):
        """
        Returns relative humidity in percent and temperature in celsius as a tuple, in that order
        If using DHT11, temperature is +/- 2 degrees
        If using DHT11, relative humidity is +/- 5%
        """
        holder = (None, None)

        while None in holder:
            holder = Adafruit_DHT.read(self.sensor.type, self.sensor.pin)
            time.sleep(0.5)

        return holder

    def c_to_f(self, temperature):
        """Returns temperature in fahrenheit"""
        return (temperature * 1.8) + 32

    def f_to_c(self, temperature):
        """Returns temperature in celsius"""
        return (5 / 9) * (temperature - 32)

    # calculations per: https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
    def get_heat_index(self, relative_humidity, temp_f):
        """Returns heat index, which is also known as Felt Air Temperature or Feels Like, in fahrenheit"""
        heat_index = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (relative_humidity * 0.094))

        if heat_index < 80:
            return heat_index

        else:
            heat_index = (
                -42.379
                + (2.04901523 * temp_f)
                + (10.14333127 * relative_humidity)
                - (0.22475541 * temp_f * relative_humidity)
                - (0.00683783 * temp_f ** 2)
                - (0.05481717 * relative_humidity ** 2)
                + (0.00122874 * temp_f ** 2 * relative_humidity)
                + (0.00085282 * temp_f * relative_humidity ** 2)
                - (0.00000199 * temp_f ** 2 * relative_humidity ** 2)
            )

        if relative_humidity > 85 and temp_f in range(80, 85):
            heat_index += ((relative_humidity - 85) / 10) * ((87 - temp_f) / 5)  # added to HI before returning

        elif relative_humidity < 13 and temp_f in range(80, 112):
            heat_index -= ((13 - relative_humidity) / 4) * math.sqrt((17 - abs(temp_f - 95)) / 17)

        return heat_index

    # calculations per: https://web.archive.org/web/20200212215746im_/https://www.vaisala.com/en/system/files?file=documents/Humidity_Conversion_Formulas_B210973EN.pdf
    # which was referenced here: https://earthscience.stackexchange.com/questions/16570/how-to-calculate-relative-humidity-from-temperature-dew-point-and-pressure
    def get_dew_point(self, relative_humidity, temp_c):
        """Returns dew point temperature in celsius"""
        # first calculate water vapour saturation pressure over water/ice in hPa
        if temp_c in range(-70, 0):
            A, m, Tn = 6.114742, 9.778707, 273.1466

        elif temp_c in range(0, 51):
            A, m, Tn = 6.116441, 7.591386, 240.7263

        Pws = A * 10 ** ((m * temp_c) / (temp_c + Tn))

        # next derive the water vapour pressure
        Pw = (Pws * relative_humidity) / 100
        # finally, calculate the dew point
        Td = Tn / ((m / math.log10(Pw / A)) - 1)

        return Td

    # calculations per: https://www.omnicalculator.com/physics/wet-bulb#how-to-calculate-the-wet-bulb-temperature
    # which cites this work: https://journals.ametsoc.org/view/journals/apme/50/11/jamc-d-11-0143.1.xml
    def get_wet_bulb(self, relative_humidity, temp_c):
        """Returns wet bulb temperature in celsius"""
        WB = (
            temp_c * math.atan(0.151977 * ((relative_humidity + 8.313659) ** 0.5))
            + math.atan(temp_c + relative_humidity)
            - math.atan(relative_humidity - 1.676331)
            + (0.00391838 * ((relative_humidity) ** (3 / 2))) * math.atan(0.023101 * relative_humidity)
            - 4.686035
        )

        return WB
