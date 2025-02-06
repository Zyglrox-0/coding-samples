import sys
import subprocess
import time

def check_return_code():
    """
    Check the return code of the last executed command and update the status variable in accordance to the error
    """
    global STATUS
    if int(sys.argv[1]) != 0:
        print(f"ERROR: retval {sys.argv[1]} : {sys.argv[2]}")
       
        if STATUS == 0:
            STATUS = int(sys.argv[1])

        if len(sys.argv) > 3:
            for item in sys.argv[3:]:
                print(f"output: {item}")

def main():
    """Main function to check disk status and gather data."""
    global STATUS
    STATUS = 0
    disk = "sda"
   
    if len(sys.argv) > 1 and sys.argv[1] != '':
        disk = sys.argv[1]
   
    nvdimm = "pmem"
    if nvdimm in disk:
        print(f"Disk {disk} appears to be an NVDIMM, skipping")
        sys.exit(STATUS)
   
    # Check /proc/partitions, exit with fail if disk isn't found
    value = subprocess.run(["grep", "-w", disk, "/proc/partitions"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.argv = [None, value.returncode, f"Disk {disk} not found in /proc/partitions"]
    check_return_code()
   
    # Check /proc/diskstats
    value = subprocess.run(["grep", "-w", "-q", "-m", "1", disk, "/proc/diskstats"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.argv = [None, value.returncode, f"Disk {disk} not found in /proc/diskstats"]
    check_return_code()
   
    # Verify the disk shows up in /sys/block/
    value = subprocess.run([f"ls /sys/block/*{disk}*"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.argv = [None, value.returncode, f"Disk {disk} not found in /sys/block"]
    check_return_code()
   
    # Verify there are stats in /sys/block/{disk}/stat
    value = subprocess.run(["test", "-s", f"/sys/block/{disk}/stat"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.argv = [None, value.returncode, f"stat is either empty or nonexistent in /sys/block/{disk}/"]
    check_return_code()
   
    # Get some baseline stats for use later
    proc_stat_begin = subprocess.getoutput(f"grep -w -m 1 {disk} /proc/diskstats")
    sys_stat_begin = subprocess.getoutput(f"cat /sys/block/{disk}/stat")

    # Generate some disk activity using hdparm -t
    subprocess.run(["hdparm", "-t", f"/dev/{disk}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
   
    # Sleep 5 to let the stats files catch up
    time.sleep(5)
   
    # Make sure the stats have changed:
    proc_stat_end = subprocess.getoutput(f"grep -w -m 1 {disk} /proc/diskstats")
    sys_stat_end = subprocess.getoutput(f"cat /sys/block/{disk}/stat")
   
    if proc_stat_begin != proc_stat_end:
        value = 0
    else:
        value = 1

    sys.argv = [None, value, "Stats in /proc/diskstats did not change", proc_stat_begin, proc_stat_end]
    check_return_code()
    sys.argv = [None, value, f"Stats in /sys/block/{disk}/stat did not change", sys_stat_begin, sys_stat_end]
    check_return_code()
   
    if STATUS == 0:
        print(f"PASS: Finished testing stats for {disk}")
   
    sys.exit(STATUS)

if __name__ == "__main__":
    main()
