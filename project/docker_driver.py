import argparse
import os
import sys,time

if sys.version_info >= (3,):
	try:
		import stdlib_list
	except:
		os.system('pip3 install stdlib_list')
		import stdlib_list

REQ_FILE = 'requirements.txt'
DOCKER_FILE = 'Dockerfile'

SRC_FILE_PATH = ''

def parseArgs():
	'''
		Parse and validate the args passed in on the command line.
	'''

	global SRC_FILE_PATH

	parser = argparse.ArgumentParser(description='Configure a Docker container in which to run your app.')
	parser.add_argument('-s', '--src', help='The path to your source code directory')
	parser.add_argument('-f', '--file', help='The name of your main Python file in the source directory including the extension')
	parser.add_argument('-a', '--args', nargs='+', help='Command line args to pass in to your Python file. Wrap the arg in double quotes. \
														 If the first arg contains a hyphen, use a leading space in the string.\n \
														 Example --args \" -a 1 -b 2 -c 3\" ')
	parser.add_argument('-r', action='store_true', help='Attempt to generate the requirements.txt file. Otherwise it is expected \
														that it exists in the PWD.')
	args = parser.parse_args()

	valid_input = True

	# Validate the source directory arg
	if args.src:
		if not os.path.exists(args.src):
			print("The source directory <%s> does not exist" % args.src)
			valid_input = False
		elif not os.path.isdir(args.src):
			print("<%s> is not a directory" % args.src)
			valid_input = False
	else:
		print("Must enter a source directory")
		valid_input = False

	# Validate the file arg
	if args.file:
		SRC_FILE_PATH = os.path.join(args.src, args.file)

		if not os.path.exists(SRC_FILE_PATH):
			print("The source file <%s> does not exist" % args.file)
			valid_input = False
		elif not os.path.isfile(SRC_FILE_PATH):
			print("<%s> is not a Python source file" % args.file)
			valid_input = False
	else:
		print("Must enter a Python source file")
		valid_input = False

	# Validate the -r arg
	if args.r and sys.version_info < (3,):
		print("Must use Python 3 for the -r option.")
		valid_input = False
	elif not args.r and not os.path.exists(REQ_FILE):
		print("Make sure a requirements.txt file exists in the working directory or use the -r option.")
		valid_input = False

	return None if valid_input == False else args

def parseFile():
	'''
		Parse the module names from the main Python file.
	'''

	lines = None
	modules = []
	exclude_strings = ['import', 'from', ',', '', ' ']

	with open(SRC_FILE_PATH, 'r') as file:
		lines = [l.strip() for l in file.readlines()]

	for line in lines:
		
		if 'import ' in line and "'import'" not in line and "\"import\"" not in line and '#' not in line:
			
			for word in line.split(' '):
				word = word.strip(',')
				if word == 'as': break
				if 'from' in line and word == 'import': break

				if word not in exclude_strings and word not in modules:

					# In case module names separated by , w/o spaces
					if ',' in word: 
						w_list = word.split(',')
						for w in w_list:
							w = w.strip()
							if w not in exclude_strings and w not in modules:
								modules.append(w)
					elif '.' in word:
						w_list = word.split('.')
						w = w_list[0].strip()
						if w not in exclude_strings and w not in modules:
								modules.append(w)
					else:
						modules.append(word)

	return modules

def getDependencies():
	'''
		Determine the dependencies needed to include in the requirements.txt file.
	'''

	dependencies = []
	modules = parseFile()
	
	for module in modules:
		if module not in stdlib_list.stdlib_list(): 
			dependencies.append(module)
	return dependencies

def createReqsFile(dependencies):
	if os.path.exists(REQ_FILE):
		os.remove(REQ_FILE)

	if len(dependencies) == 0: return

	with open(REQ_FILE, 'w') as file:
		for dep in dependencies:
			file.write(dep + '\n')

def createDockerFile(args):
	'''
		Create the Dockerfile using the appropriate args.
	'''

	if os.path.exists(DOCKER_FILE):
		os.remove(DOCKER_FILE)

	with open(DOCKER_FILE, 'w') as file:
		file.write('FROM python:3.5' + '\n\n')
		file.write('WORKDIR /project \n\n')

		if os.path.exists(REQ_FILE):
			file.write('COPY requirements.txt . \n\n')
			file.write('RUN pip3 install -r requirements.txt\n\n')

		file.write('COPY {}/ . \n\n'.format(args.src))
		file.write('CMD [ \"python\", \"./{}\"'.format(args.file))

		if args.args:
			arg_string = ''
			for arg in args.args:
				arg_string += ', \"{}\"'.format(arg.strip())
			file.write(arg_string)
		file.write(' ]\n')

def main():
	'''
		The main function for running an app in the Docker container.
	'''

	print
	print('\nParsing arguments...')
	args = parseArgs()

	if args == None:
		exit(-1)
	
	if args.r:
		print('Parsing %s for module dependencies...' % SRC_FILE_PATH)
		dependencies = getDependencies()
		print('Creating %s...' % REQ_FILE)
		createReqsFile(dependencies)

	print('Creating %s...' % DOCKER_FILE)
	createDockerFile(args)

	image = '{}-image'.format(args.file)
	os.system('docker build -t {} .'.format(image))

	print('\nRunning Docker container...')
	print('\nRunning %s...\n' % args.file)
	os.system('docker run --rm {}'.format(image))

	stream = os.popen('echo Returned output')
	output = stream.read()
	output

	print('\nFinished running %s...\n' % args.file)

	# Remove the Docker image used for this test
	os.system('docker image rm --force {}'.format(image))

	print('\nFinished cleanup...\n')

if __name__ == '__main__':
	main()
