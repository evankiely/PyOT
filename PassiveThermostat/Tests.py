# This is basically a sanity check I used to compare my calculations against online sources/calculators
# This allowed me to validate the equations as written in the Thermometer class

import Adafruit_DHT

from Classes import Sensor, Thermometer

dht11 = Adafruit_DHT.DHT11

indoors = Thermometer(Sensor(17, dht11, "Indoors"))
outdoors = Thermometer(Sensor(27, dht11, "Outdoors"))

in_RH, in_temp = indoors.get_rh_and_temp()
out_RH, out_temp = outdoors.get_rh_and_temp()

print(f"INDOORS TEMP (C) AND RH: {in_temp}, {in_RH}")
print(f"OUTDOORS TEMP (C) AND RH: {out_temp}, {out_RH}")

in_as_f, out_as_f = indoors.c_to_f(in_temp), outdoors.c_to_f(out_temp)
in_back_to_c, out_back_to_c = indoors.f_to_c(in_as_f), outdoors.f_to_c(out_as_f)

print(f"INDOORS ORIGINAL (C): {in_temp}, AS F: {in_as_f}, CONVERTED BACK TO C: {in_back_to_c}")
print(f"OUTDOORS ORIGINAL (C): {out_temp}, AS F: {out_as_f}, CONVERTED BACK TO C: {out_back_to_c}")

in_heat_index = indoors.get_heat_index(in_RH, in_as_f)
out_heat_index = outdoors.get_heat_index(out_RH, out_as_f)

print(f"INDOORS HEAT INDEX (F): {in_heat_index}, OUTDOORS HEAT INDEX (F): {out_heat_index}")

in_dew_point = indoors.get_dew_point(in_RH, in_temp)
out_dew_point = outdoors.get_dew_point(out_RH, out_temp)

print(f"INDOORS DEW POINT (C): {in_dew_point}, OUTDOORS DEW POINT (C): {out_dew_point}")

in_dew_point_c = indoors.c_to_f(in_dew_point)
out_dew_point_c = outdoors.c_to_f(out_dew_point)

print(f"INDOORS DEW POINT (F): {in_dew_point_c}, OUTDOORS DEW POINT (F): {out_dew_point_c}")

in_wet_bulb = indoors.get_wet_bulb(in_RH, in_temp)
out_wet_bulb = outdoors.get_wet_bulb(out_RH, out_temp)

print(f"INDOORS WET BULB (C): {in_wet_bulb}, OUTDOORS WET BULB (C): {out_wet_bulb}")

in_wet_bulb_f = indoors.c_to_f(in_wet_bulb)
out_wet_bulb_f = outdoors.c_to_f(in_wet_bulb)

print(f"INDOORS WET BULB (F): {in_wet_bulb_f}, OUTDOORS WET BULB (F): {out_wet_bulb_f}")
