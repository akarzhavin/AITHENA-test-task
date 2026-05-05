Questions for the Technical Specifications

FAQ

The code I received already fulfills the conditions in task.md
Can you recommend a test database?
Is it worth considering cases where JS code is stored in a file with a .py extension?
The scancode library is well-suited for parsing licenses; ast for determining the number of functions; and LLMs for rewriting files into Rust.
Should I use these tools or prefer LLMs for all cases?
1. Architecture and Infrastructure (System Design)
1.1. Scale, Scaling and Cost
What is the expected volume of input data (data/ folders)? If we plan to analyze thousands of files, this critically affects decisions about parallelization and rate-limiting.
Are there budget constraints on API calls? Each file requires at least 1–2 LLM calls.
Time constraints (SLA): "Are there requirements for the pipeline execution speed? Should the analysis of a typical repository (e.g., 1000 files) be completed in 5 minutes, 1 hour, or can it run all night?"
File size (Context Window Limit): "What to do with huge files (e.g., generated bundle.js with 50,000 lines)? They won't fit in the LLM context window. Ignore, truncate, or try to split into chunks?"
1.2. LLM Infrastructure, Security and Deployment
Should the LLM provider be replaceable/abstracted?
Do current security regulations allow the transfer of source code to third-party cloud services (e.g., OpenAI)? In case of restrictions, it is advisable to implement support for local LLMs (such as Llama 3 or Ollama). This will not only ensure the possibility of on-premise system deployment but also help optimize operating costs.
1.3. Fault Tolerance and Idempotency
LLM API is an external service. Should our pipeline support a Checkpointing/Idempotency mechanism? If the network drops in the middle of the process, the system should not re-send already successfully analyzed files upon restart.
What to do if the LLM returns an incorrect/invalid response? Retry? Skip the file? Fail?
Can a file be unreadable (binary, corrupted)? What do we do in this case?
Is partial output needed — if 2 out of 3 files were processed and the 3rd failed?
1.4. Component Selection: LLM vs. Deterministic Algorithms (Trade-offs)
How justified is the use of LLM for extracting method names and arguments? 
Traditional AST parsers provide high accuracy, speed, and no execution costs, however, they are strictly tied to the grammar of specific languages and are unable to process invalid code. In turn, LLMs work slower, require an API budget, and are prone to hallucinations, but guarantee multi-language support and tolerance to syntax errors "out of the box".
Which architectural pattern do we choose:
Use exclusively deterministic algorithms (AST) for structural analysis, consciously limiting the stack of supported languages?
Rely on LLM for the entire pipeline for maximum versatility and ease of implementation?
Implement a hybrid approach (Fallback): priority fast parsing via AST with switching to LLM in case of errors or when working with unsupported extensions?

2. Business Logic Detailing and Success Criteria
2.1. License Classification
What to do with files without a license at all? The task describes only permissive and copyleft. The Pydantic model will need to be updated.
How to handle proprietary/commercial licenses?


A specific list of licenses needs to be approved! 
How to classify MPL? The task.md says "GPL and similar" (the prompt classifies MPL as copyleft). Clarify the specific list.
How to handle proprietary/commercial licenses?
Suggestion: Use a ready-made database (e.g., SPDX) instead of LLM for custom and rare licenses to avoid the need to manually prescribe the division into permissive and copyleft.
What to do with dual-license files (when two licenses are specified)?
2.2. Function Extraction
Whether to consider nested functions, lambdas, class methods? The task says "function names" but does not specify the scope.
How to classify a variable number of arguments (e.g., *args, **kwargs in Python or ...rest parameters in JS)?
Language support: For which languages is support needed (JS and Python)? Which file extensions to support (.py, .js, .ts, .jsx, .tsx)?
What if there are no functions in the file?
What to do with overloaded / overridden functions?
In data/2.py the function bar1(c) is defined twice. Should the duplicate function be considered when choosing a branch between extract function names and rewrite file in rust.
Is it necessary to remove the duplicate function when calculating the output?
File 3.py contains JavaScript code. How to determine the file language? — by extension or by content?
2.3. Rewriting in Rust
What is the success criterion for the generated Rust code? Should it be just a "syntactic draft" at the text level (best-effort), or must the code compile successfully?
What are the expectations if the source code uses heavyweight frameworks (e.g., Django, React) that the LLM cannot rewrite 1-to-1 in Rust?
