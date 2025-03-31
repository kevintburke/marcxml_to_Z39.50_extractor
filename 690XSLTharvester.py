import random
import subprocess as sbp
import unidecode as undc
import re

#Generate four-digit random ID to avoid file overwriting
random.seed()
FILE_ID = str(random.randint(1111,9999))
FILE_NAME = str(f'querybuilder{FILE_ID}.xslt')
print(f'Session id is {FILE_ID}.')

#Create xslt file template with random id in name
def createxslt():
    f = open(FILE_NAME, 'w')
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<xsl:stylesheet version="1.0"\nxmlns:xsl="http://www.w3.org/1999/XSL/Transform">\n<xsl:output method="text" encoding="utf-8" omit-xml-declaration="yes" indent="no" />\n\n<xsl:template match = "/">\n\t<xsl:for-each select="collection/record">')
    f.close()

#Collect user input of parameters to search and process
def get_input():
    #Prompt user for search parameters in plain text.
    params = input("Input parameters for search, separated by spaces. Options include: 'Author', 'ISBN', 'LCCN', 'PubDate', 'Publisher', 'Title': ")

    #Split input at spaces
    param = params.split()

    #Check that input is in list of valid inputs.
    for element in param:
        #Render user input case insensitive
        element = str.upper(element)
        if element in ['AUTHOR', 'ISBN', 'LCCN', 'PUBDATE', 'PUBLISHER', 'TITLE']:
            print('Parameter selected: ', element)
        else:
            print("Invalid input: ", element)
            quit

    #Convert param to MARC fields/subfields
    fields = []

    for element in param:
        ##ADD ISSN (DASH DOESN'T MATTER), 1XX AND 7XX FOR AUTHOR?, 1035 ANYWHERE FOR 035/095? LANGUAGE REQUIREMENT MATCHING RECORD AT 008 35-37? NOT SURE HOW TO ADD RELATIONSHIP ATTRIBUTES (@attr 2=???)
        #Render user input case insensitive... again...
        element = str.upper(element)
        if element == 'AUTHOR':
            fields.append(('100',('a','b','c','d'),'1003'))
        elif element == 'ISBN':
            fields.append(('020','a','7'))
        elif element == 'LCCN':
            fields.append(('010','a','9'))
        elif element == 'PUBDATE':
            fields.append(('260','c','31'))
            fields.append(('264','c','31'))
        elif element == 'PUBLISHER':
            fields.append(('260','b','1018'))
            fields.append(('264','b','1018'))
        elif element == 'TITLE':
            fields.append(('245',('a','b'),'4'))
        else:
            print('Unable to identify parameter')
            break

    #Sort fields/subfields
    fields.sort()
    
    #Print MARC Fields and Subfields and Bib-1 Equivalents
    print('Fields, Subfields, and Bib-1 Attributes: ', fields)

    return fields

#Add blocks to XSLT file for each parameter, including delimiters for repeating fields
def write_xslt(fields):
    f = open(f'{FILE_NAME}','a')
    for field, subfield, query in fields:
        f.write(f"""
        <xsl:for-each select="datafield[@tag='{field}']">
            <xsl:text>@attr 1={query} "</xsl:text>""")
        for code in subfield:
            f.write(f"""
            <xsl:value-of select="subfield[@code='{code}']" />
            <xsl:text> </xsl:text>""")
        f.write("""
        <xsl:text>" </xsl:text>
        </xsl:for-each>""")
        
    f.write("""
    <xsl:text>&#xD;&#xA;</xsl:text>
    </xsl:for-each>
</xsl:template>
</xsl:stylesheet>""")

#Run XSLTPROC in the command line and save output as txt file
def run_xsltproc():
    #Open records file and check for errors
    records = None
    while records == None:
        records = input("Enter the name OR absolute path of the records to be processed: ")
        try:
            open(records, 'r')
            break
        except Exception as e:
            records = None
            print(f'Error: {e}. Please confirm the file name and try again.')
            continue

    #Run xsltproc in commandline using subprocess
    sbp.run(f'xsltproc -o queryterms{FILE_ID}.txt {FILE_NAME} {records}')
    print(f'Output saved as queryterms{FILE_ID}.txt')

#Add operators to query strings conditional on terms, following Polish notation
def add_operators():
    #Create file to receive formatted query
    o = open(f'query{FILE_ID}.txt','w', encoding = 'utf-8')
    #Open query file and read line-by-line
    f = open(f'queryterms{FILE_ID}.txt', 'r', encoding = 'utf-8')
    line = f.readline()
    #Add operators @and/@or to correct positions in lines based on numbers and types of query terms
    while line != "":
        #Remove empty terms
        line = re.sub(r'@attr 1=\d+ " " ', '', line)
        line = re.sub(r' {2,}', '', line)
        #Remove lines with only one term
        if line.count("@attr") <= 1:
            line = f.readline()
            continue
        #Handle addition of @or for repeated publication information terms using slicing to find first iteration
        if line.count("@attr 1=1018") > 1 or line.count("@attr 1=31") > 1 or line.count("@attr 1=7") > 1:
            #Set empty variables for counts of terms needing @or
            count1 = 0
            count2 = 0
            count3 = 0
            #Handle multiple instances of publisher
            if line.count("@attr 1=1018") > 1:
                count1 = line.count("@attr 1=1018") - 1
                line = line[:line.index("@attr 1=1018")] + ("@or " * count1) + line[line.index("@attr 1=1018"):]
            #Handle multiple instances of pub date
            if line.count("@attr 1=31") > 1:
                count1 = line.count("@attr 1=31") - 1
                line = line[:line.index("@attr 1=31")] + ("@or " * count1) + line[line.index("@attr 1=31"):]
            #Handle multiple instances of ISBN
            if line.count("@attr 1=7") > 1:
                count1 = line.count("@attr 1=7") - 1
                line = line[:line.index("@attr 1=7")] + ("@or " * count1) + line[line.index("@attr 1=7"):]
            terms = line.count("@attr") - (count1 + count2 + count3)
            line = ("@and " * (terms - 1)) + line
            line = undc.unidecode(line)
            o.write(line)
        #Simple @and add for queries without multiple pub terms
        else:
            terms = line.count("@attr")
            line = ("@and " * (terms - 1)) + line
            line = undc.unidecode(line)
            o.write(line)
        line = f.readline()

    print(f'Final query saved as query{FILE_ID}.txt')    

#Create main function
def main():
    createxslt()
    fields = get_input()
    write_xslt(fields)
    run_xsltproc()
    add_operators()

#Run main function
if __name__ == "__main__":
    main()