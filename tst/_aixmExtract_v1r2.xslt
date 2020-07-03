<?xml version="1.0" encoding="UTF-8"?>
<?altova_samplexml .\20200618_aixm4.5_Eurocontrol-FR.xml?>
<?altova_samplexml .\aixm4.5_SIA-FR_2020-04-23.xml?>
<?altova_samplexml .\aixm4.5_Eurocontrol-FR_2019-11-07.xml?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="xml" indent="yes" encoding="UTF-8"/>
	
	<xsl:variable name="outputFileName"><xsl:text>_aixmExtract_outputData.xml</xsl:text></xsl:variable>
	<xsl:variable name="alphabet">AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZzÀàÁáÂâÃãÄäÅåÆæÇçÈèÉéÊêËëÌìÍíÎîÏïÐðÑñÒòÓóÔôÕõÖöØøÙùÚúÛûÜüÝýÞþ</xsl:variable>
	<xsl:variable name="minuscule">aabbccddeeffgghhiijjkkllmmnnooppqqrrssttuuvvwwxxyyzzaaaaaaaaaaaaææcceeeeeeeeiiiiiiiiððnnooooooooooøøuuuuuuuuyyþþ</xsl:variable>
	<xsl:variable name="msgNoFound"><xsl:text>msg:Aucun resultat associé à la demande...</xsl:text></xsl:variable>
	
	<xsl:key name="keyOrgUidTxtName" match="//*/Uni/OrgUid/txtName/text()" use="." />
	<xsl:key name="keyCodeDistVerUpper" match="//*/Ase/codeDistVerUpper/text()" use="." />
	<xsl:key name="keyCodeDistVerLower" match="//*/Ase/codeDistVerLower/text()" use="." />
	
	<xsl:template match="/">
		<!-- <xsl:variable name="ret" select="//*/Ase[txtName='FRANCE UIR']"/> -->
		<!-- <xsl:variable name="ret" select="//*/Ase[contains(txtName,'BALE')]"/>  -->
		<!-- <xsl:variable name="ret" select="//*/Ase[contains(translate(txtName,$alphabet,$minuscule),'clermont')]"/>  -->
		
		<xsl:result-document method="xml" href="{$outputFileName}">
			<xsl:element name="showResults">
				<xsl:apply-templates select="//*/Ase[contains(translate(txtName,$alphabet,$minuscule),'luxeuil')]"/>
				<!-- <xsl:apply-templates select="//*/Gbr"/> -->
				<!-- <xsl:apply-templates select="//*/Ase[not(valDistVerLower)]"/> -->
				<!-- <xsl:apply-templates select="//*/Ase[not(txtName)]"/> -->
				<!-- <xsl:apply-templates select="//*/Ase[(AseUid/codeType='D-OTHER') and not(codeClass)]"/> -->
				
				<!-- Sortie d'une sélection unique d'éléments (en relation avec la définition de la <xsl:key ...> définie plus haut)-->
				<!-- <xsl:for-each select="//*/Uni/OrgUid/txtName/text()[generate-id() = generate-id(key('keyOrgUidTxtName',.)[1])]">-->
				<!-- 
				<xsl:for-each select="//*/Ase/codeDistVerLower/text()[generate-id() = generate-id(key('keyCodeDistVerLower',.)[1])]">
					<li>
						<xsl:value-of select="."/>
					</li>
				</xsl:for-each>
				<xsl:for-each select="//*/Ase/codeDistVerUpper/text()[generate-id() = generate-id(key('keyCodeDistVerUpper',.)[1])]">
					<li>
						<xsl:value-of select="."/>
					</li>
				</xsl:for-each>
				-->
			</xsl:element>
		</xsl:result-document>
	</xsl:template>

	<xsl:template match="Gbr">
		<xsl:copy-of select="."/>
		<xsl:variable name="mid" select="./GbrUid/@mid"/>
		<!-- <xsl:element name="tst"><xsl:value-of select="./AseUid/@mid"/></xsl:element> 
		<xsl:apply-templates select="//*/Abd[AbdUid/AseUid/@mid=$mid]"/>  -->
	</xsl:template>
	
	<xsl:template match="Ase">
		<xsl:copy-of select="."/>
		<xsl:variable name="mid" select="./AseUid/@mid"/>
		<!-- <xsl:element name="tst"><xsl:value-of select="./AseUid/@mid"/></xsl:element> -->
		<xsl:apply-templates select="//*/Abd[AbdUid/AseUid/@mid=$mid]"/>
	</xsl:template>

	<xsl:template match="Abd">
		<!-- <xsl:element name="tst"><xsl:value-of select="./AbdUid/AseUid/@mid"/></xsl:element> -->
		<xsl:copy-of select="."/>
	</xsl:template>
	
</xsl:stylesheet>
