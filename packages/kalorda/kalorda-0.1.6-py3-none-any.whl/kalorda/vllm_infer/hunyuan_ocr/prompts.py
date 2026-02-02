hunyuan_prompt = {
    "Spotting": "Detect and recognize text in the image, and output the text coordinates in a formatted manner.",
    "Document_Parsing": "Extract all information from the main body of the document image and represent it in markdown format, ignoring headers and footers. Tables should be expressed in HTML format, formulas in the document should be represented using LaTeX format, and the parsing should be organized according to the reading order.",
    "General_Parsing": "Extract the text in the image.",
    "Information_Extraction": "Output the value of Key.<br><br>• Extract the content of the fields: ['key1','key2', ...] from the image and return it in JSON format.<br><br>• Extract the subtitles from the image.",
    "Translation": "First extract the text, then translate the text content into English. If it is a document, ignore the header and footer. Formulas should be represented in LaTeX format, and tables should be represented in HTML format.",
}
