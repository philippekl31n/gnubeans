❯ have a think about the user experience of this project; what does installation and execution look like?                                                                                                 
                                                                                                                                                                                                          
⏺ A few things shape the UX here:                                                                                                                                                                         
                                                                                                                                                                                                          
  The core use case is a one-time migration. The user has a .gnucash file, wants a .beancount file, runs the tool once (maybe a few times while tuning), then never again. Installation friction matters, 
  but not as much as for a daily-use tool. Output quality and transparency about what was dropped/renamed matter a lot.                                                                                   
                                                                                                                                                                                                          
  Ideal installation:                                                                                                                                                                                     
  pipx install abswedge                                                                                                                                                                                   
  pipx is the modern standard for Python CLI tools — isolates dependencies, makes the command globally available, no virtualenv management. Publishing to PyPI gets you there. uv tool install abswedge is
   the emerging alternative for users on newer tooling.                                                                                                                                                   
                                                                                                                                                                                                          
  Ideal execution:                                                                                                                                                                                        
  abswedge ledger.gnucash                                                                                                                                                                                   
  # writes 2025.beancount alongside the input, warnings to stderr                                                                                                                                         
  With stdout mode for composability:                                                                                                                                                                     
  abswedge ledger.gnucash | bean-check -                                                                                                                                                                    
                                                                                                                                                                                                          
  The input should be accepted in either form (.gnucash compressed or .gnucash.xml decompressed) transparently — the user shouldn't have to know or care about the internal format.                       
                                                                                                                                                                                                          
  Warnings matter. The converter will make judgment calls — sanitizing account names, dropping business-module entities, computing lot costs. All of these should be reported to stderr as named warnings 
  so the user knows what to review in the output. Something like:                                                                                                                                         
  WARNING: account "Vanguard Total Bond Market Index Fund Admiral Shares" → "Vanguard-Total-Bond-Market-Index-Fund-Admiral-Shares"                                                                      
  WARNING: commodity "1234567" is not a valid Beancount symbol — renamed to "C1234567"                                              
  WARNING: 3 business-module entities (invoices, customers) dropped                                                                                                                                       
                                                                                                                                                                                                          
  The output should pass bean-check out of the box, or the tool should tell you exactly why it doesn't. A migration tool that produces invalid output creates more work than it saves.                    
                                                                                                                                                                                                          
  One design question this surfaces: should beancount itself be a hard dependency (using beancount.core for output construction and running bean-check automatically), or should the tool write raw text  
  and leave validation to the user? Using beancount.core gives you correctness guarantees but ties you tightly to beancount 2.x vs. 3.x. Writing validated plain text and making beancount optional keeps 
  the tool lighter and version-agnostic.                                                                                                                                                                  
                  
  Want to resolve that and add it to design-decisions.md? 