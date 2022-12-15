#!/usr/bin/python

# dictionaries to strings using json
import json

# to send requests to server
import requests

# for command-line arguments
import sys 

# all the crypto stuff is here
import tommieutils as tu

import copy
import time

######### YOUR CODE HERE ############
def getAllUsedCoins(chain):
    used = []
    for block in chain['blocks']:
        currtrans = block['transactions']
        if (currtrans['transtype']=='1'):
            currins = [(x['transid'],x['outnum']) for x in currtrans['ins']]
            used.extend(currins)
    return used

def isAvailCoin(inpair, chain):
    #coin (repr. by a pair (blocknum,outnum)) is available if it has never appeared in an ins list
    used = getAllUsedCoins(chain)
    if (inpair in used):
        return False
    return True

def findLastMined(chain):
    """
    return the block index/id containing most recent mined transaction
    used by isValidMinedTrans, since a valid mined transaction must have id of previous mined trans.
    """
    numblocks = len(chain['blocks'])
    i = numblocks-1
    while (i>=0):
        if (chain['blocks'][i]['transactions']['transtype']=='2'):
            break
        i -= 1
    return i

# an empty Pay Transaction.
emptyPayTrans = {
    'transtype' : '1',
    'ins' : [],
    'outs' : [],
    'sigs' : []
}

def genPay(pk,sk, inlist, pklist, amtlist, remainder):
    """
    You might want to complete this to use in your wallet

    inlist should be list of pairs, with (transid, outnum)
    inlist should be spendable by same user (who has pk,sk as key)
    this function does not have any restrictions enforced (i.e., shouldn't call isValidTrans), those will be checked before creating a block, so output of this function could be rejected by server
    """
    trans = copy.deepcopy(emptyPayTrans)
    
    
    out = {'recipient': tu.sha256(pklist[0]), 'value': sum(amtlist) - remainder}
    trans['outs'].append(out)

    out = {'recipient': tu.sha256(pklist[1]), 'value': remainder}
    trans['outs'].append(out)

    for transid, outnum in inlist:
	ins = {'outnum': outnum, 'transid': transid}
	trans['ins'].append(ins)

    sign = [{'pk': pk, 'signature': tu.sign(sk, json.dumps(trans, sort_keys=True))}]
    trans['sigs'] = sign
    
    return trans

# only valid if prevmine is id of block with the most recent mined transaction 
# SHA256(nonce||SHA256(trans with nonce set to '')) should be hex that starts with six 0s
emptyMinedTrans = {
    'prevmine' : '',
    'transtype' : '2',
    'outs': [],
    'nonce' : '',
    'timestamp':''
}

def genMined(beneficiarypk, prevmine):
    """
    You will want to write this function, probably in your wallet
    """
    trans = copy.deepcopy(emptyMinedTrans)
    nonce = 0
    
    trans['prevmine'] = str(prevmine)
    trans['outs'] = [{'recipient': tu.sha256(beneficiarypk), 'value': 50}]
    trans['timestamp'] = str(time.time())

    transHash = tu.sha256(json.dumps(trans, sort_keys=True))

    while tu.sha256(str(nonce) + transHash)[:6] != "000000":
    	nonce = nonce + 1

    trans['nonce'] = str(nonce)

    return trans 





pk = open(sys.argv[1], 'r').read()
sk = open(sys.argv[2], 'r').read()
hashPK = tu.sha256(pk)
running = True

while running:
	userCoins = []
	coinsValue = []
	r = requests.get('http://127.0.0.1:8080/showchainraw')
	currChain = json.loads(r.text)


	for block in currChain['blocks']:
		index = 0
		currtrans = block['transactions']

		for outs in currtrans['outs']:
			if(outs['recipient'] == hashPK and isAvailCoin((int(block['id']), index), currChain) == True):
				userCoins.append((int(block['id']), index))
				coinsValue.append(outs['value'])
			index = index+1

	print('Welcome, ' + sys.argv[1][7:8].upper() + sys.argv[1][8:len(sys.argv[1]) - 6] + '.')
	print('Your current Tommiecoin amount is: ' + str(sum(coinsValue)))
	input = raw_input("What would you like to do (pay, mine, quit): ")

	if input.lower() == "pay":
		pklist =[]
		amtlist = []
		inlist = []
		users = ['alice', 'bob', 'carlos', 'dawn', 'eve']
		userstring = '(Alice, Bob, Carlos, Dawn, Eve)'
		enoughmoney = True
	
		input = raw_input('Who would you like to pay?' + userstring + ': ')
		if input.lower() not in users:
			print('No such user')
		else:
			pklist.append(open("./keys/" + input.lower() + "pk.txt" , "r").read())
			pklist.append(pk)
			input = int(raw_input('How much would you like to pay (must be integer): '))

			while input > 0:
				if len(userCoins) == 0:
					print('Not enough TommieCoin')
					enoughmoney = False
					break
			
	
				input = input - max(coinsValue)
				inlist.append(userCoins.pop(coinsValue.index(max(coinsValue))))
				amtlist.append(coinsValue.pop(coinsValue.index(max(coinsValue))))

 			if enoughmoney == True:
				print('Building transaction...')
			
				payment = json.dumps(genPay(pk, sk, inlist, pklist, amtlist, abs(input)), sort_keys=True)
				push = requests.post('http://127.0.0.1:8080/addtrans', data={'trans': payment})
			
				if push.status_code == 200:
					print('Success!')
				else:
					print('Failed Request')

	
	elif input.lower() == "mine":
		print("Mining coins...")

		mineattempt = json.dumps(genMined(pk, findLastMined(currChain)), sort_keys=True)
		push = requests.post('http://127.0.0.1:8080/addtrans', data={'trans': mineattempt})
		
		if push.status_code == 200:
			print('Success!')
		else:
			print('Failed Request')	
	elif input.lower() == "quit":
		exit()