import os
from math import floor

class NFA:
	def __init__(self, states, symbols, transitions, start, accepting):
		self.states = states
		self.symbols = symbols
		self.transitions = transitions
		self.bake_transitions()
		self.start = start
		self.accepting = accepting
	def bake_transitions(self):
		trans = {}
		for t in self.transitions:
			if (t[0], t[1]) in trans:
				trans[(t[0], t[1])] += [t[2]]
			else:
				trans[(t[0], t[1])] = [t[2]]
		self.transitions = trans
	def run(self, data):
		d = [str(x) for x in data]
		s = [(self.start, 0)]
		tokens = []
		iter = 0
		while len(d) > 0:
			iter += 1
			cur = d[0]
			del d[0]
			s_prime = []
			for x in s:
				if (x[0], cur) in self.transitions:
					s_prime += [(y, x[1]) for y in self.transitions[(x[0], cur)]]
			s = list(set(s_prime))
			acc = [x for x in s if x[0] in self.accepting]
			for x in acc:
				tokens.append((x[0], x[1], iter))
			s.append((self.start, iter))
		return tokens

def read_nfa(path):
	with open(path, 'r') as f:
		sections = [s.strip() for s in f.read().split('-----')]
	states = sections[0].split('\n')
	symbols = sections[1].split('\n')
	transitions = sections[2].split('\n')
	transitions = [x.split(' ') for x in transitions]
	start = sections[3]
	accepting = sections[4].split('\n')
	return NFA(states, symbols, transitions, start, accepting)

overlap = lambda dice, x, y: False if (x[0] == 'run5s' and x[2] - x[1] == 6 and y[0] == 'five' and dice.count(5) == 2) or (y[0] == 'run5s' and y[2] - y[1] == 6 and x[0] == 'five' and dice.count(5) == 2) else x[2] > y[1] and x[1] < y[2]

def interpret(dice, tokens):
	interp = [[]]
	for t in tokens:
		found = False
		for i, j in enumerate(interp):
			if not (len(j) > 0 and overlap(dice, t, j[-1])):
				interp[i].append(t)
				found = True
		if not found:
			l = len(interp)
			for i in range(l):
				interpretation = [x for x in interp[i]]
				while len(interpretation) > 0 and overlap(dice, interpretation[-1], t):
					del interpretation[-1]
				interp.append(interpretation + [t])
	l = list(set([tuple(i) for i in interp]))
	result = []
	for i in l:
		good = True
		for j in l:
			if i != j:
				if all([x in j for x in i]):
					good = False
					break
		if good:
			result.append(i)
	return result

def printerpret(t):
	for x in t:
		print(x)

def p(subspace, superspace):
	return len(subspace) / len(superspace)

def make_space(dice):
	if dice == 1:
		return [[i] for i in range(1, 7)]
	else:
		return [i + [j] for i in make_space(dice - 1) for j in range(1, 7)]

avg = lambda x: sum(x) / len(x)

scores = {}
with open('ten_thousand_scores.txt', 'r') as f:
	score_text = f.read().split('\n')
	for line in score_text:
		kvp = line.split(' ')
		scores[kvp[0]] = int(kvp[1])

space = [make_space(i) for i in range(1, 7)]

nfa = read_nfa('ten_thousand_nfa.txt')

print('Generating roll scans...')

rolls = {}
for s in space:
	rolls = {**rolls, **{tuple(y) : interpret(y, nfa.run([str(z) for z in list(sorted(y))])) for y in s}}

print('Generating failure array...')

max_score = 100000

failure = [p([x for x in space[i] if len(rolls[tuple(x)][0]) == 0], space[i]) for i in range(6)]

totals = [0, 0, 0, 0]

nsi = lambda s, d: Ens[d - 1][int(min(max_score, s) / 50)]

si = lambda s, d: (1 - 2 * failure[d - 1]) * s if s > max_score else Est[d - 1][int(s / 50)]

si_adjusted = lambda s, d: ((1 - 2 * failure[d - 1]) * s if s > max_score else Est[d - 1][int(s / 50)]) + s * (1 - fi(d))

def nss(s, d, v):
	Ens[d - 1][int(min(max_score, s) / 50)] = v

def ss(s, d, v):
	Est[d - 1][int(min(max_score, s) / 50)] = v

fi = lambda x: failure[x - 1]

def subsets(l):
	result = []
	upper = (2**len(l))
	for j in range(1, upper):
		result.append([x for i, x in enumerate(l) if j & (2**i) > 0])
	return result

def E(s, d):
	expectation = 0
	for x in space[d - 1]:
		maximal = float('-inf')
		interp = rolls[tuple(x)]
		if len(interp[0]) == 0:
			maximal = -s
		else:
			for inter in interp:
				subset = subsets(list(inter))
				for subs in subset:
					score = sum([scores[item[0]] for item in subs])
					dice = d - sum([item[2] - item[1] for item in subs if scores[item[0]] > 0])
					if dice == 0:
						dice = 6
					score += nsi(s + score, dice)
					maximal = max(maximal, score)
		expectation += (1 / len(space[d - 1])) * maximal
	return max(0, expectation)

def Es(s, d):
	expectation = 0
	for x in space[d - 1]:
		maximal = float('-inf')
		interp = rolls[tuple(x)]
		if len(interp[0]) == 0:
			maximal = -s
		else:
			for inter in interp:
				subset = subsets(list(inter))
				for subs in subset:
					score = sum([scores[item[0]] for item in subs])
					dice = d - sum([item[2] - item[1] for item in subs if scores[item[0]] > 0])
					if dice == 0:
						dice = 6
					score += si(s + score, dice)
					maximal = max(maximal, score)
		expectation += (1 / len(space[d - 1])) * maximal
	return max(-s * (1 - fi(d)), expectation)

def optimal_choice(s, d, steal):
	maximal = float('-inf')
	maximal_choice = None
	maximal_index = None
	interp = rolls[tuple(d)]
	if len(interp[0]) == 0:
		return ('nothing', 0)
	else:
		for inter in interp:
			subset = subsets(list(inter))
			for subs in subset:
				score = sum([scores[item[0]] for item in subs])
				dice = len(d) - sum([5 if item[0] == 'run5' or item[0] == 'run5s' else item[2] - item[1] for item in subs])
				if dice == 0:
					dice = 6
				if steal == 0:
					score += nsi(s + score, dice)
				else:
					score += si(s + score, dice)
				if score > maximal:
					maximal = score
					maximal_choice = subs
					if steal == 0:
						maximal_index = nsi(s + sum([scores[item[0]] for item in subs]), dice)
					else:
						maximal_index = si_adjusted(s + sum([scores[item[0]] for item in subs]), dice)
	if maximal_index == 0:
		return ('hold', maximal_choice)
	return ('roll', maximal_choice)

if os.path.isfile('Ens.txt'):
	with open('Ens.txt', 'r') as f:
		lines = f.read().split('\n')
	Ens = [[float(x) for x in line.split(' ')] for line in lines]
else:
	print('Calculating non-steal expected values...')
	Ens = [([0] * int(max_score / 50)) + [0] for i in range(6)]
	for score in list(reversed(range(int(max_score / 50)))):
		for dice in range(1, 7):
			nss(score * 50, dice, E(score * 50, dice))
			print('Done ' + str(score) + ', ' + str(dice) + ': ' + str(nsi(score * 50, dice)))
	with open('Ens.txt', 'w') as f:
		content = '\n'.join([' '.join([str(x) for x in row]) for row in Ens])
		f.write(content)

if os.path.isfile('Est.txt'):
	with open('Est.txt', 'r') as f:
		lines = f.read().split('\n')
	Est = [[float(x) for x in line.split(' ')] for line in lines]
else:
	print('Calculating steal expected values...')
	Est = [([0] * int(max_score / 50)) + [(1 - 2 * failure[i]) * max_score] for i in range(6)]
	for score in list(reversed(range(int(max_score / 50)))):
		for dice in range(1, 7):
			ss(score * 50, dice, Es(score * 50, dice))
			print('Done ' + str(score) + ', ' + str(dice) + ': ' + str(si(score * 50, dice)))
	with open('Est.txt', 'w') as f:
		content = '\n'.join([' '.join([str(x) for x in row]) for row in Est])
		f.write(content)

print('Done!')

steal_val = lambda: min(2, floor(max(totals) / 3000))

def play():
	global totals
	for i in range(len(totals)):
		totals[i] = 0
	score = 0
	totals[1] += int(input('Enter P2 score: '))
	totals[2] += int(input('Enter P3 score: '))
	sc = int(input('Enter P4 score: '))
	totals[3] += sc
	player_turn = False
	stealing_turn = False
	while True:
		stolen = False
		if steal_val() > 0 and not player_turn:
			d = int(input('Enter number of stealable dice: '))
			val = sc + nsi(sc, d)
			if steal_val() == 2:
				val = sc + si(sc, d)
			if val > si(0, 6):
				score += sc
				stolen = True
				stealing_turn = True
				print('Steal')
			else:
				print('Don\'t steal')
		player_turn = True
		user_input = input('Enter dice values: ')
		if user_input == 'q':
			break
		dice = [int(i) for i in user_input.split(' ')]
		choice, score_increase = optimal_choice(score, dice, 0 if stealing_turn and steal_val() == 1 else steal_val())
		if choice == 'hold':
			if stolen:
				totals[3] -= sc
			print('Take ' + str(score_increase) + ' and bank with score ' + str(score + sum([scores[item[0]] for item in score_increase])))
			if steal_val() > 0:
				if (stealing_turn and steal_val() == 1) or input('Stolen (y/n)? ') == 'n':
					totals[0] += score + sum([scores[item[0]] for item in score_increase])
			else:
				totals[0] += score + sum([scores[item[0]] for item in score_increase])
			score = 0
			totals[1] += int(input('Enter P2 score: '))
			totals[2] += int(input('Enter P3 score: '))
			sc = int(input('Enter P4 score: '))
			totals[3] += sc
			print('Scores: ' + str(totals))
			player_turn = False
			stealing_turn = False
		elif choice == 'nothing':
			score = 0
			print('Lost')
			totals[1] += int(input('Enter P2 score: '))
			totals[2] += int(input('Enter P3 score: '))
			sc = int(input('Enter P4 score: '))
			totals[3] += sc
			print('Scores: ' + str(totals))
			player_turn = False
			stealing_turn = False
		else:
			if stolen:
				totals[3] -= sc
			score += sum([scores[item[0]] for item in score_increase])
			print('Take ' + str(score_increase))
			print('Score: ' + str(score))