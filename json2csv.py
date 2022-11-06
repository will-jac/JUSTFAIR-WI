import os
import json
import pandas as pd
import sys

if len(sys.argv) == 1:
    caseYear = int(input("Enter the data year: "))
    caseType = input("Enter the case type: ")
else:
    caseYear = int(sys.argv[1])
    caseType = sys.argv[2]

path = f"data/{caseYear}/{caseType}/"
if not os.path.exists(path):
    raise Exception(f"Folder path not found, please check that {path} exists")

output_path = f"processed_data/"
print(f"Writing out data to: {output_path}")
os.makedirs(output_path, exist_ok=True)

file_names = os.listdir(path)

# pd.append is being deprecated
cases_output = []
charges_output = []

sent_keys = ["jail", "prison", "probation", "life"]
# other sentencing options that I'm ignoring: "license revoked", "ignition interlock", "supervision"
ignore_keys = ["fine", "costs", "other sentence"]

time_units = {
    # "day": 365,
    "days": 365,
    "weeks": 52,
    # "month": 12,
    "months": 12,
    "years": 1,
}

# convert a time of the form "53 Days" or "10 months" or "12 years" to an integer year amount
# also supported: "1 Years, 6 Months"
def parse_time(time_str):
    life_count = 0
    int_time = 0
    for t in time_str.split(", "):
        try:
            amount, unit = t.split(" ")
            if unit.lower() == "life":
                life_count += int(amount)
            else:
                int_time += int(amount) / time_units[unit.lower()]
        except:
            print(f"[{time_str}]")
            raise Exception
        
    return int_time, life_count

for file in file_names:
    with open(path+file, mode="r") as f:
        data = json.load(f)
        if "errors" in data:
            print(f"\tMissing data for {path}{file} (file has error), skipping")
            continue
        if "result" not in data:
            print(f"\tBad data for {path}{file}, (no results) skipping")
            continue
        if data["result"]["available"] == False:
            print(f"\tData not available for {path}{file}, Reason: {data['result']['reason'] }")
            continue

        try:
            # print(data_json_format)
            result = data["result"]

            case_row = {}
            case_row["caseNo"] = result["caseNo"]
            case_row["countyNo"] = result["countyNo"]
            case_row["countyName"] = result["countyName"]
            defendant = result["defendant"]
            case_row["defendantName"] = defendant["name"]
            case_row["defendantRace"] = defendant["race"]
            case_row["defendantSex"] = defendant["sex"]
            case_row["defendantDob"] = defendant["dob"]
            case_row["judgeName"] = result["respCtofc"]

            max_charge = None
            agg_charge = {k: 0 for k in sent_keys}

            # for each charge
            if "charges" in result:
                for charge in result["charges"]:
                    charge_row = {}

                    charge_row["caseNo"] = result["caseNo"]
                    charge_row["countyNo"] = result["countyNo"]

                    charge_row["crimeName"] = charge["descr"]
                    charge_row["crimeDate"] = charge["offenseDate"]
                    charge_row["crimeStatute"] = charge["statuteCite"]
                    charge_row["crimeSeverity"] = charge["severity"]
                    
                    # for each judgment associated with the charge

                    # ASSUME that judgments / supervisions for 1 charge will not carry multiple of the same penalty
                    # eg that there will be only 1 supervision for jail across all the judgments/supervisions for this charge
                    charge_sent = {}

                    judgments_delim = ""
                    for judgment in charge["judgments"]:
                        # if this is re-opening the sentence, ignore it 
                        # we may care about this in the future, but right now, this isn't part of the original sentence
                        if judgment["reOpenedEvent"] is not None: continue

                        if len(judgment['supervisions']) == 0: continue
                        
                        # for each part of the judgment
                        for i,supervision in enumerate(judgment['supervisions']):
                            # if no time, ignore it
                            if supervision['time'] is None: continue

                            # Don't do the below - only use the ORIGINAL sentences
                            # if notes say to ignore, ignore it!
                            if supervision['notes'] is not None:
                                ignore = False
                                for k in ["resentenced", "vacates"]:
                                    if k in supervision['notes'].lower(): 
                                        ignore = True
                                        break
                                if ignore:
                                    continue

                            # TODO: we should check for exact concurrency, not just if it can be done concurrently with something
                            # EG: can be done concurrently with a different case but not this one
                            conc = supervision['notes'] is not None and 'concurrent' in supervision['notes'].lower()

                            descr = supervision['descr'].lower()
                            matched = False
                            for k in sent_keys:
                                if k in descr:
                                    sent_time = parse_time(supervision["time"])
                                    # ASSUME that if a charge has two identical sentences, it is probable them re-opening it
                                    # and not actually 2 consecutive sentences
                                    # see: data/2016/CF/2016CF000012-49.json
                                    if k in charge_sent and charge_sent[k][0] != sent_time:
                                        # if they have identical dates, assume it's an error
                                        # just take the first one
                                        # see: data/2016/CF/2016CF000036-69.json
                                        if charge_sent[k][1] != judgment["orderDate"]: 
                                            print("duplicate,", k, "already in", charge_sent)
                                            print(charge["judgments"])
                                            raise Exception
                                    
                                    charge_sent[k] = (sent_time, judgment["orderDate"], conc)
                                    matched = True

                            judgments_delim = judgments_delim + f"{supervision['descr']},{supervision['time']};"

                        # now, we have the sentence associated with the judgment
                        # currently only storing prison, jail, probation
                        # but this could easily be extended

                    charge_row["judgments"] = judgments_delim
                    charge_row["pleaDate"]	= charge["pleaDate"]
                    charge_row["pleaDescr"] = charge["pleaDescr"]
                    default = ((0,0), None, False)
                    for k in sent_keys:
                        # check for bad data
                        (time, life), _, conc = charge_sent.get(k,default)
                        if k != "prison":
                            if life != 0:
                                print(charge_sent)
                                raise Exception
                        charge_row[k] = time
                        charge_row[k+"_concurrent"] = conc
                        
                        # add to the aggregate unless it's concurrent
                        if conc and agg_charge[k] <= charge_row[k]: continue

                        agg_charge[k] += charge_row[k]

                    charge_row["life"] = charge_sent.get("prison",default)[0][1]
                    agg_charge["life"] += charge_row["life"]

                    # check the max
                    if max_charge is None: 
                        max_charge = charge_row
                    else:
                        if charge_row["life"] > max_charge["life"]: max_charge = charge_row
                        elif max_charge["life"] == 0 and charge_row["prison"] > max_charge["prison"]: 
                            max_charge = charge_row
                        elif max_charge["life"] == 0 and max_charge["prison"] == 0 and charge_row["jail"] > max_charge["jail"]: 
                            max_charge = charge_row
                        elif max_charge["life"] == 0 and max_charge["prison"] == 0 and max_charge["probation"] == 0 and charge_row["probation"] > max_charge["probation"]: 
                            max_charge = charge_row

                    charges_output.append(charge_row)

            if max_charge is not None:
                case_row["maxChargeCrimeName"] = max_charge["crimeName"]
                case_row["maxChargeCrimeDate"] = max_charge["crimeDate"]
                case_row["maxChargeCrimeStatute"] = max_charge["crimeStatute"]
                case_row["maxChargeCrimeSeverity"] = max_charge["crimeSeverity"]
                case_row["maxChargePleaDate"] = max_charge["pleaDate"]
                case_row["maxChargePleaDescr"] = max_charge["pleaDescr"]

                for k in sent_keys:
                    case_row[f"maxCharge{k.capitalize()}"] = max_charge[k]

            for k in sent_keys:
                case_row[f"aggregateCharge{k.capitalize()}"] = agg_charge[k] 
            
            case_row["numCharges"] = len(result["charges"])

            cases_output.append(case_row)
        except:
            print(f"Could not process {path+file}")
            # print(data_json_format)
            raise Exception()
        
cases_df = pd.DataFrame.from_records(cases_output)
cases_df.to_csv(output_path + f"/{caseYear}-{caseType}-cases-compiled.csv")

charges_df = pd.DataFrame.from_records(charges_output)
charges_df.to_csv(output_path + f"/{caseYear}-{caseType}-charges-compiled.csv")