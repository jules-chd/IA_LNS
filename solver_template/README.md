# Solver interface

The solver must contain an entrypoint file __main.py__ taking two command line arguments. It must be possible to run the solver as follows:

```
python3 main.py <instance-file-path> <solution-file-path>
```

The following is guaranteed for the evaluation:

 * The above-mentioned command will be used to run your solver on each tested instance
 * Current working directory will be set to the base directory of your solver
 * Absolute paths will be provided as arguments

Your solver must read the instance file from path given by <instance-file-path> and save the best found solution to <solution-file-path>. Formats of the instances and solution JSON files are described separately in the __../data/README.md__.

# Evaluation environment

The evaluation will be held on __aisa.fi.muni.cz__. Please make sure that everything works properly in this environment (with no additional modules loaded). Before testing the code prior to your submission on __aisa.fi.muni.cz__, make yourself familiar with the rules which apply to longer calculations (https://www.fi.muni.cz/tech/unix/computation.html.en). Namely, it is required to set lower priority to your calculation (command __nice__). Note that the evaluation run will be also executed under the __nice__ command.

# Solver implementation

The solver is required to be coded in Python 3.

We recommend you to structure your solver into multiple files.

## Libraries

Only libraries available in standard Python 3 installation are allowed. Namely, importing libraries like __json__, __math__, __sys__, __time__ or __random__ is OK. Libraries requiring separate installation, i.e., running ``pip install <library-name>``, are forbidden (e.g., __numpy__).

## Code template

The provided package contains a simple template for your solver. The template is compliant with the described interface and was tested on __aisa.fi.muni.cz__.

Since your implementation is required to stick with a given timeout, the template also provides an example of a timeout mechanism you can use.


## Generative AI

Using generative AI tools is allowed under the following conditions:

 * AI tools are only used to generate well-testable functions
 * Each AI-generated function is covered with a human-written unit test
 * Each such usage is clearly described and documented in the report
   * Persistent links to the relevant conversations with AI are provided
   * You may only use AI tools that provide this functionality (e.g., ChatGPT)

The main point of this restriction is to allow you to use AI tools while emphasizing the need to explicitly control the correctness of their outputs. Thus, using AI is purely optional.


## Misc

Using the field __best_cost__ from the instance file is forbidden within the implementation of your solver. This information is only provided for your reference and comparison with your own solutions.


# Submission recommendations

Before you submit your work, verify that your ZIP archive works on __aisa.fi.muni.cz__ as intended. Take the archive to be submitted, extract it on __aisa.fi.muni.cz__, and test your solver running the given command on some instances. 

It is important (especially for Windows users) to verify the submission ZIP rather than a git repository clone as git tends to convert between Windows and Linux end of lines. Windows-style end of lines may be problematic on __aisa.fi.muni.cz__ so make sure that the ZIP is OK in this regard.

Both stdout and stderr will be collected during the evaluation. Make sure that your solver does not produce excessive amounts of logging information. It is definitely OK to log the evolution of your objective function and similar information, but please refrain from logging whole solutions or very detailed information on the progress of your search.
