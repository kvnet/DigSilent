import os
import powerfactory # Importieren des DigSilent Powerfactory Moduls

# Powerfactory-Objekte festlegen
app = powerfactory.GetApplication() # Application-Objekt
script = app.GetCurrentScript() # Aktives Powerfactory-Skript-Objekt

# ************** KONSTANTEN **************
# PowerFactory spezifische Klassen- und Verzeichnisnamen
sDiagramProjectFolder = "dia"
sIntGrfnetClassName = "IntGrfnet"
sVisTitleClassName = "VisTitle"
sSetTitmClassName = "SetTitm"
sSetTitParamName = "SetTit"
# Tuple-Liste aller Parameter eines *.SetTitm-Objektes von PowerFactory
tTitleAttributes = ("nproj", "anex", "cong1", "cong2", "subt1", \
    "sub1z", "sub2z", "sub3z", "date_user", "date_ssys", "date_str", "FileName")
# String-Variable für den Skript-Eingabeparameter "Selection"
sSelectionParamName = "Selection"


# ************** DEFINITIONEN / METHODEN **************
def GetScriptAttributeNames(sAttribute = ""):
    # Definition zur Überprüfung, ob der übergebene Parameter im Skript vorhanden ist.

    # Übergabeparameter:
    #   Einzelner optionaler Name der gesuchten Skript-Variable als String, Standardwert = ""

    # Rückgabe:
    #   Liste der ermittelten Variablennamen des Skripts.
    #   Wenn Übergabeparameter Leer, dann werden alle Namen der Skript-Variablen ausgegeben.

    lScriptParams = script.IntName
    # Überprüfen, ob der übergebene Parametername Leer ist
    # Wenn Ja -> Alle Namen der Skript-Variablen zurückgeben
    #if sParameter == "": return [p for p in script.IntName]
    if sAttribute == "": return lScriptParams
    # Liste des Namens der gesuchten Skript-Variablen zurückgeben
    if sAttribute in lScriptParams:
        return [sAttribute]
    else:
        app.PrintError(f"Der benötigte Eingabeparametername '{sAttribute}' existiert nicht" + \
            " im aktiven Skript!")
        return []

def CheckSetTitmAttributes(oSetTitm = None):
    # Definition zur Überprüfung eines 'SetTitm'-Objektes auf
    # dessen Vollständigkeit seiner Attribute gemäß
    # Tuple-Liste 'tTitleAttributes'

    # Übergabeparameter:
    #   Ein SetTitm-Objekt, Standardwert = None

    # Rückgabe:
    #   Boolschen Wert

    # Wenn kein SetTitm-Objekt übergeben wurde, oder das übergebene Objekt
    # ist keine SetTitm-Klasse, dann wird eine Fehlermeldung aus- und 
    # als Ergebnis 'Falsch' zurückgegeben
    if not(oSetTitm) or (oSetTitm.GetClassName() != sSetTitmClassName): 
        app.PrintError(f"Fehlendes Klassenobjekt: {sSetTitmClassName}!")
        return False

    # Liste für fehlende Parameter anlegen
    lstErr = []
    # Alle Attribute der Tuple-Liste 'tTitleAttributes' durchlaufen
    for p in tTitleAttributes:
        try:
            # Versuch zur Ermittlung eines Werten aus dem entsprechenden Attribut 
            v = oSetTitm.GetAttribute(p)
        except:
            # Wenn Versuch des Auslesen fehlschlägt, wird der entsprechende
            # Attributname zur Fehlerliste hinzugefügt
            lstErr.append(p)

    # Wenn Fehlerliste nicht lerr ist, wird diese als Warnung aus- und 
    # als Ergebnis 'Falsch' zurückgegeben
    if (lstErr):
        app.PrintError(f"Fehlendes Attribute des Klassenobjekts '{sSetTitmClassName}': " + \
            lstErr)
        return False
    
    return True

def ConvertStringsToList(sFilter = ""):
    # Definition zur Umwandlung eines Komma-getrennten Strings
    # in eine Liste

    # Übergabeparameter:
    #   Ein kommagetrennter String

    # Rückgabe:
    #   Liste mit Einzelstrings

    lFilter = str(sFilter).split(",")
    # Die Methode strip () gibt eine Kopie der Zeichenfolge zurück,
    # in der alle Zeichen vom Anfang und Ende der Zeichenfolge
    # entfernt wurden (Standard-Whitespace-Zeichen).
    return [f.strip() for f in lFilter]

def GetSelectedDiagrams(lFilter = ""):
    # Definition zum Auslesen der Diagrmm-Objekte im
    # Projektverzeichnis "Diagramme"

    # Übergabeparameter:
    #   lFilter: Liste von Strings, nach welchem in Diagrammnamen gesucht werden soll

    # Rückgabe: 
    #   Liste von PowerFactory-Diagramm-Objekten

    # Alle Diagramm-Objekte des Diagram-Projektverzeichnisses in eine Liste laden
    lAllDiagrams = app.GetProjectFolder(sDiagramProjectFolder).GetContents()
    lDiagrams = []

    for sFilter in lFilter:
        # Wenn sFilter gleich "*" oder leer werden alle Diagramm-Objekte zurück gegeben
        if sFilter == "*" or sFilter == "":
            lDiagrams = lAllDiagrams
            break # Schleife verlassen
        else:
            # List Comprehension
            lDiagrams += [oDiagram for oDiagram in lAllDiagrams \
                if sFilter in oDiagram.loc_name]

    return lDiagrams

def GetVisTitle(oDiagram):
    # Definition zum Auslesen des VisTitle-Objektes aus einem Diagramm

    # Übergabeparameter:
    #   oDiagram: Diagramm-Objekt

    # Rückgabe: 
    #   VisTitle-Objekt. Wenn keine VisTitle-Objekt im Diagramm vorhanden ist,
    #   wird eine Warnmeldung aus- und "None" zurückgegeben

    # Wenn kein Diagramm-Objekt übergeben wurde oder die Klasse des Objektes
    # nicht eines Diagrammes entspricht, Fehlermeldung aus- und Nichts zurückgeben
    if (oDiagram == None) or (oDiagram.GetClassName() != sIntGrfnetClassName):
        app.PrinError(f"Fehlendes Diagramm-Objekt!")
        return

    # Ermitteln der VisTitle-Objekte des Diagrammes
    lVisTitles = oDiagram.GetContents("*." + sVisTitleClassName, 1)

    if (lVisTitles):
        return lVisTitles[0] # Erstes VisTitle-Objekt zurückgeben
    else:
        sErr = "Die Grafik: '{}' enthält kein '*.{}'-Objekt!"
        app.PrintWarn(sErr.format(oDiagram.loc_name, sVisTitleClassName))
        return # Nichts zurückgeben

def GetSetTitm(oVisTitle, oDiagram):
    # Definition zum Auslesen des SetTitm-Objektes aus einem VisTitle-Objekt

    # Übergabeparameter:
    #   oVisTitle: VisTitle-Objekt
    #   oDiagram: Diagramm-Objekt

    # Rückgabe: 
    #   SetTitm-Objekt (Titel). Wenn keine SetTitm-Objekt im VisTitle-Objekt vorhanden ist,
    #   wird eine Warnmeldung aus- und "None" zurückgegeben

    # Wenn kein VisTitle-Objekt oder Diagramm-Objekt übergeben wurde,
    # Fehlermeldung aus- und Nichts zurückgeben
    if (oVisTitle == None) or (oDiagram == None): 
        app.PrintError(f"Fehlendes Diagramm-Objekt und/oder VisTitle-Objekt!")
        return

    # Ermitteln des SetTit-Parameters des VisTitle-Objektes
    oSetTitm = oVisTitle.SetTit

    if oSetTitm != None:
        return oSetTitm # Erstes VisTitle-Objekt zurückgeben
    else:
        sErr = "Die Grafik: '{}' enthält kein '*.{}'-Objekt!"
        app.PrintWarn(sErr.format(oDiagram.loc_name, sSetTitmClassName))
        return None # Nichts zurückgeben

def SetTitleAttributes(oSetTitm):
    # Definition/methode zum Schreiben der Skript-Parameter in ein
    # SetTitm-Objekt

    # Übergabeparameter:
    #   oSetTitm: SetTitm-Objekt

    # Rückgabe: 
    #   Boolschen Wert

    # Überprüfen des oSetitm-Objektes auf Vollständigkeit seiner Attribute
    if not(CheckSetTitmAttributes(oSetTitm)): return False
    
    # Laden alle der Eingabeparameter-Variablennamen des aktiven Skripts in eine Liste
    lScriptAttributes = GetScriptAttributeNames()
    # Schnittmenge der gleichen Attributnamen der Skript-Variablen und der
    # Titel-Attribute
    lSetupAttributes = set(tTitleAttributes).intersection(set(lScriptAttributes))

    if (lSetupAttributes):
        for sAttrib in lSetupAttributes:
            sOldAttVal = oSetTitm.GetAttribute(sAttrib)
            sNewAttVal = script.GetAttribute(sAttrib)

            if (sNewAttVal != "") and (sNewAttVal != sOldAttVal):
                # Schreiben der neuen Werte in den Schriftkopf
                oSetTitm.SetAttribute(sAttrib, sNewAttVal)
                # Informationszeilentext
                sInfo = f"   ----> {sAttrib}: '{sOldAttVal}' --> '{sNewAttVal}'"
                app.PrintInfo(sInfo)
        
        return True
    else:
        return False

# ************** CODE **************

# Überprüfen ob der Eingabeparameter "Selection" im aktiven Skript vorhanden ist
lScriptAttributes = GetScriptAttributeNames(sSelectionParamName)
# Wenn die Liste 'lScriptAttributes' leer ist (= Attribute-Name ist nicht vorhanden)
# wird das Programm verlassen
if not(lScriptAttributes): exit()

# Auslesen des String-Wertes des Eingabeparamters "Selection" aus dem Skript
sFilter = script.GetAttribute(sSelectionParamName)
# Übergeben des String-Wertes an den StringToListConverter um eine Liste
# aller einzelnen Werte zu erhalten
lFilter = ConvertStringsToList(sFilter)

# Durchlauf aller Diagramm-Objekte
for oDiagram in GetSelectedDiagrams(lFilter):

    app.PrintInfo("Korrigiere Schriftkopf in Grafik '{}': ".format(oDiagram.loc_name))

    oVisTitle = GetVisTitle(oDiagram)
    oSetTitm = GetSetTitm(oVisTitle, oDiagram)

    if oSetTitm != None:
        x = SetTitleAttributes(oSetTitm)
