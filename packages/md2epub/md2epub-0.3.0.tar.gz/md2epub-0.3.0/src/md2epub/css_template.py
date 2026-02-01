
KDP_CSS = """
/* KDP Standard CSS */

/* General Body Style */
body {
    font-family: "Caecilia", "Palatino", "Georgia", serif;
    font-size: 1.0em;
    line-height: 1.2;
    margin: 0;
    text-align: justify;
}

/* Headings */
h1 {
    font-size: 2.0em;
    font-weight: bold;
    text-align: center;
    margin-top: 2em;
    margin-bottom: 1em;
    page-break-before: always;
}

h2 {
    font-size: 1.5em;
    font-weight: bold;
    margin-top: 1.5em;
    margin-bottom: 0.8em;
}

h3 {
    font-size: 1.3em;
    font-weight: bold;
    margin-top: 1.2em;
    margin-bottom: 0.6em;
}

/* Paragraphs */
p {
    margin-top: 0;
    margin-bottom: 0;
    text-indent: 1.5em;
}

/* First paragraph shouldn't be indented */
h1 + p, h2 + p, h3 + p, hr + p {
    text-indent: 0;
}

/* Blockquotes */
blockquote {
    font-size: 0.9em;
    font-style: italic;
    margin: 1em 2em;
    padding-left: 1em;
    border-left: 2px solid #ccc;
    text-indent: 0;
}

/* Code Blocks */
pre {
    background-color: #f5f5f5;
    padding: 0.5em;
    font-family: monospace;
    font-size: 0.9em;
    white-space: pre-wrap; /* Wrap long lines */
    text-indent: 0;
    margin: 1em 0;
}

code {
    font-family: monospace;
}

/* Scenes/Separators */
hr {
    border: 0;
    border-top: 1px solid #000;
    margin: 2em auto;
    width: 50%;
}

.scene-break {
    text-align: center;
    margin: 2em 0;
    font-size: 1.2em;
    font-weight: bold;
    text-indent: 0;
}

.asterisk-break {
    text-align: center;
    margin: 2em 0;
    font-size: 1.2em;
    text-indent: 0;
}

/* Images */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

/* Front Matter */
.title-page {
    text-align: center;
    margin-top: 30%;
}

.copyright-page {
    font-size: 0.8em;
    text-align: center;
    margin-top: 40%;
}

.dedication {
    font-style: italic;
    text-align: center;
    margin-top: 20%;
}

.acknowledgement {
    margin-top: 5%;
}
"""
