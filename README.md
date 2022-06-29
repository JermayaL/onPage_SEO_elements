# onPage_SEO_elements
SEO on page elementen: H1, H2, Title tag, Meta description, Image (lazy-loading True/False), preload/prefetch/preconnect, slug, lastParagraph, First 100 words, keyword density (also per word). Input xlsx: URL en zoekwoord.


**Steps**

1. Delete the output.csv. It does not overwrite it.
2. Change vars.txt: just copy the folder where the input_for_script.xlsx is located. In your case: input_file='your_path_here'
3. **Make sure you have python > 3.8 installed:** == https://www.python.org/downloads/ 
4. Open prompt (windows) or terminal (mac)

Do the following in prompt or terminal:

1. First, go to the script path where the python script is located. Script can only run if the terminal/prompt is on the same location as the script. Go to the script folder (as first most of the times in Downloads folder) and do right click and then 'show info'. There you will see the _location_.
2. pip install -r requirements.txt
3. pip install python-slugify
4. python kw_search.py

Now it opens Chromium and goes through any URL you put in the input xlsx. The output is: output.csv.
