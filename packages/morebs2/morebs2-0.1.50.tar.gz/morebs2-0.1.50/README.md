MOREBS
=======
Is a collection of methods and classes written in Python to aid in data generation, specifically
vector data. Important classes include:
- `BallComp`
- `ResplattingSearchSpaceIterator`

For the source code to this project's latest version, go to 
`https://github.com/changissz/morebs`.

For a mathematics paper on the `BallComp` algorithm, see the link  
`https://github.com/changissnz/ballcomp`. 

Documentation for project can be found at `_build/html`. Documentation 
first needs to be built. The library Sphinx for generating the documentation
is required to be installed. 

# Updates For Project On and Off 

# Update: 5/25/25 #3 
Deleted the project DER from Github. The project was the original work I did 
before I refactored it into `morebs`, and has been sitting dead on Github for 
a while. 

# Update: 5/25/25 #2 
So the new version is up on Github (0.1.1). I also took the step to delete the 
`s*.txt` files that were present from a few commits back. The files were relatively 
large, and I must have forgotten to exclude the files from being committed to Github. 

# Update: 5/25/25 

I have not done much serious work on this project since February of 2023. 
Recently, I was working with directed graphs and decided to contribute 
some code for that topic to this project. I still remember the ideas that 
started this project, geometric intersection and data generation. On 
geometric intersection, the Schopenhauer wrote about it in his book, The 
World as Will and Representation. Even though he did not go into mathematical 
detail on it, his words left an inspiring impact on my computing thought. The 
topic of data generation is a pretty big field in computing. Cloud computing, 
especially, has been a big driver for big data analytics, the counter-active 
field to data generation. Now that there are present and emerging regulations 
regarding the "fair" and "benign" use of data in artificial intelligence and 
related fields, data generation has become very important to some enterprises 
that wish to train their artificial intelligence systems, but do not have 
authentic datasets in adequate quantity. I'm not surprised that no one has 
decided to help contribute code to this project. Not to mean any insult, but 
big data, machine learning, that kind of stuff really is not a normal person's 
interest (sorry, populists). Besides, most open-source projects that really take 
off are heavily funded. I have been out of the academic environment for almost 
half a decade now. Big data, machine learning, that kind of stuff, was mainly an 
academic business. It still is, pretty much, because all I ever read about from 
technology corporations is their business products, consumer-side. 

I was reviewing some of the code in this project. The project definitely needs 
more thorough documentation as well as unit-testing. `morebs` was originally 
a project solely for the `BallComp` algorithm and a data generator, one that 
travels along an n-dimensional lattice, called `NSDataInstruction`.
`NSDataInstruction` uses the `ResplattingSearchSpaceIterator` as the data structure 
that outputs preliminary values. Then I added a basic polynomial factorization 
algorithm (`PolyFactorEst`) and an n-dimensional delineation algorithm (see file 
`deline.py`). This was back in January of 2023. Not every algorithm is thoroughly 
tested, as a reminder. 

Right now, I am working on directed graphs, so that is the topic of the new code 
content for the next version of morebs2 on `pypi.org`. 