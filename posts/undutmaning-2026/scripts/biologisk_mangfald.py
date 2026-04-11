from constraint import Problem

fish = [
    ("BlueShark", 8),
    ("Manta", 7),
    ("Lionfish", 6),
    ("Oscar", 7),
    ("Angelfish1", 4),
    ("Angelfish2", 4),
    ("Goldfish", 4),
    ("Surgeon", 3),
    ("Coralfish", 3),
    ("Minnow", 3),
    ("Puffer", 2),
    ("Betta1", 2),
    ("Betta2", 2),
    ("Swordtail", 2),
    ("Goby", 2),
    ("Pleco", 2),
    ("Guppy1", 1),
    ("Guppy2", 1),
    ("Guppy3", 1),
    ("Tetra1", 2),
    ("Tetra2", 2),
    ("Tetra3", 2),
    ("Catfish", 2),
    ("Koi", 4),
    ("Clown", 3),
]

sizes = {n: s for n, s in fish}
names = [n for n, _ in fish]
TANKS = ["A", "B", "C", "D"]

problem = Problem()
for name, _ in fish:
    problem.addVariable(name, TANKS)


# Capacity
def tank_capacity(*assignments):
    totals = {t: 0 for t in TANKS}

    for fish_name, tank in zip(names, assignments):
        totals[tank] += sizes[fish_name]

    return all(total <= 20 for total in totals.values())


problem.addConstraint(tank_capacity, names)

# Large predator
large = ["BlueShark", "Manta", "Lionfish", "Oscar"]
for i in range(len(large)):
    for j in range(i + 1, len(large)):
        problem.addConstraint(lambda a, b: a != b, [large[i], large[j]])


# BlueShark stim
def shark_needs_stim(*assignments):
    placement = dict(zip(names, assignments))

    shark_tank = placement["BlueShark"]

    small_count = sum(
        1
        for f in names
        if sizes[f] <= 3 and placement[f] == shark_tank and f != "BlueShark"
    )

    return small_count == 0 or small_count >= 3


problem.addConstraint(shark_needs_stim, names)

# Environment
problem.addConstraint(lambda t: t != "D", ["BlueShark"])  # needs salt
problem.addConstraint(lambda t: t in ["B", "C"], ["Manta"])  # warm/temp salt
problem.addConstraint(lambda t: t == "C", ["Lionfish"])  # warm only
problem.addConstraint(lambda t: t == "C", ["Coralfish"])  # warm + coral
problem.addConstraint(lambda t: t != "A", ["Angelfish1"])  # not cold
problem.addConstraint(lambda t: t != "A", ["Angelfish2"])  # not cold
problem.addConstraint(lambda t: t in ["A", "D"], ["Oscar"])  # dark or brackish
problem.addConstraint(lambda t: t in ["B", "D"], ["Guppy1"])  # temperate
problem.addConstraint(lambda t: t in ["B", "D"], ["Guppy2"])  # temperate
problem.addConstraint(lambda t: t in ["B", "D"], ["Guppy3"])  # temperate
problem.addConstraint(lambda t: t == "D", ["Pleco"])  # not high salt
problem.addConstraint(lambda t: t != "A", ["Koi"])  # not cold

# Detritivore
problem.addConstraint(
    lambda p, c, k, g, gf: all(t in [p, c, k, g, gf] for t in TANKS),
    ["Pleco", "Catfish", "Koi", "Goby", "Goldfish"],
)

# Multi-fish compatibility
problem.addConstraint(lambda a, o: a != o, ["Angelfish1", "Oscar"])
problem.addConstraint(lambda a, o: a != o, ["Angelfish2", "Oscar"])
problem.addConstraint(lambda a, l: a != l, ["Angelfish1", "Lionfish"])
problem.addConstraint(lambda a, l: a != l, ["Angelfish2", "Lionfish"])

for g in ["Guppy1", "Guppy2", "Guppy3"]:
    problem.addConstraint(lambda g, o: g != o, [g, "Oscar"])
    problem.addConstraint(lambda g, l: g != l, [g, "Lionfish"])

problem.addConstraint(lambda c, l: c != l, ["Catfish", "Lionfish"])
problem.addConstraint(lambda p, s: p != s, ["Puffer", "Surgeon"])
for b in ["Betta1", "Betta2"]:
    for g in ["Guppy1", "Guppy2", "Guppy3"]:
        problem.addConstraint(lambda b, g: b != g, [b, g])

problem.addConstraint(lambda c, m: c != m, ["Coralfish", "Manta"])
problem.addConstraint(lambda c, o: c != o, ["Coralfish", "Oscar"])

# Solve
solution = problem.getSolution()
for t in TANKS:
    fish = [n for n in names if solution[n] == t]
    print(f"{t}:")
    for f in sorted(fish):
        print(f"  {f}")
