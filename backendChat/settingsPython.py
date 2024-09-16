from urllib.request import urlopen
from bs4 import BeautifulSoup


def initializeAllPythonVersions():
    global ALL_PYTHON_VERSIONS
    ALL_PYTHON_VERSIONS = []
    with urlopen('https://www.python.org/doc/versions/') as r:
        text = r.read()
        soup = BeautifulSoup(text, "html.parser")
        allPythonVersions = soup.select("#python-documentation-by-version>.simple>li>.reference")

        for pythonversion in allPythonVersions:
            ALL_PYTHON_VERSIONS.append(pythonversion.contents[0].split("Python ")[1])
        # str_1_encoded = bytes(str(pythonversionsID),'UTF-8')
        # soup2 = BeautifulSoup(str_1_encoded, "html.parser")
        #
        # este= soup2.find_all(_class="reference external")
        # soup2 = BeautifulSoup(pythonversionsID.getText(),"html.parser" )
        # print(pythonversionsID.contents[0])
        ALL_PYTHON_VERSIONS.reverse()
        #ALL_PYTHON_VERSIONS= sorted(ALL_PYTHON_VERSIONS)
    print("ALL_PYTHON_VERSIONS:concluded")

    return


def getAllPythonVersions():
    return ALL_PYTHON_VERSIONS
