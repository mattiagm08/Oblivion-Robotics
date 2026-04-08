import comm, time

comm.begin()
while True:
    print(comm.getSensors())
    time.sleep(1)