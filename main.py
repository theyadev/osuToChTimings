import os 

with open("./osu.txt", "r") as file:
    content = file.read()

content = content.split("[")
content = list(filter(lambda x: x.startswith("TimingPoint"), content))[0]
content = content.split("]")[1].split("\n")
content = list(filter(lambda x: x.strip() != "", content))
content = list(filter(lambda x: x.split(",")[-2] == "1", content))

tickRate = 192

# [Ticks, BPM, Signature, Minutes]
chTimingLines = [
    [0, 120, 4, 0]
]

for line in content:
    timing, beatLength, signature, _, _, _, _, _ = line.split(",")
    bpm = 60000 / float(beatLength)
    # print(f"Timing: {timing}, Beat Length: {beatLength} ms, Time Signature: {signature}, BPM: {bpm:.2f}")
    
    minutes = int(timing) / 60000
    minutesElapsed = minutes - chTimingLines[-1][-1]
    ticksElapsed = round(minutesElapsed * chTimingLines[-1][1] * tickRate)
    ticks = round(ticksElapsed + chTimingLines[-1][0])
    print(f"Minutes Elapsed: {minutesElapsed}, Ticks Elapsed: {ticksElapsed}, Ticks: {ticks}")
    chTimingLines.append([ticks, bpm, signature, minutes])

print(chTimingLines)

# Write to CloneHero.txt with proper formatting
with open("CloneHero.txt", "w") as file:
    for line in chTimingLines:
        ticks, bpm, signature, _ = line
        # Format: [ticks] = TS [Signature]
        file.write(f"{ticks} = TS {signature}\n")
        # Format: [TICKS] = B [BPM]000
        file.write(f"{ticks} = B {int(bpm)}000\n")


