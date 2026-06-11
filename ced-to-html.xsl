<?xml version="1.0" encoding="UTF-8"?>

<!-- Renders csp/ced.xml or csa/ced.xml as HTML.

     Usage: xsltproc ced-to-html.xsl csp/ced.xml > csp/ced.html
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html" encoding="UTF-8" doctype-system="about:legacy-compat" indent="yes"/>

  <xsl:template match="/ced">
    <html>
      <head>
        <title>
          <xsl:choose>
            <xsl:when test="unit">AP CSA Course and Exam Description</xsl:when>
            <xsl:otherwise>AP CSP Course and Exam Description</xsl:otherwise>
          </xsl:choose>
        </title>
        <style>
          body { font-family: sans-serif; line-height: 1.4; max-width: 50em; margin: 2em auto; padding: 0 1em; }
          section section { margin-left: 1.5em; }
          .id { font-weight: bold; }
          pre { background: #f4f4f4; padding: 0.5em; }
        </style>
      </head>
      <body>
        <xsl:apply-templates select="big-idea|unit"/>
      </body>
    </html>
  </xsl:template>

  <!-- Level 1: CSP big ideas / CSA units -->

  <xsl:template match="big-idea">
    <section class="big-idea" id="{@xml:id}">
      <h1>
        <xsl:text>Big Idea </xsl:text>
        <xsl:value-of select="count(preceding-sibling::big-idea) + 1"/>
        <xsl:text>: </xsl:text>
        <xsl:value-of select="title"/>
        <xsl:text> (</xsl:text>
        <xsl:value-of select="@xml:id"/>
        <xsl:text>)</xsl:text>
      </h1>
      <xsl:apply-templates select="essential-understanding"/>
    </section>
  </xsl:template>

  <xsl:template match="unit">
    <section class="unit" id="{@xml:id}">
      <h1>
        <xsl:text>Unit </xsl:text>
        <xsl:value-of select="substring-after(@xml:id, 'unit-')"/>
        <xsl:text>: </xsl:text>
        <xsl:value-of select="title"/>
      </h1>
      <xsl:apply-templates select="topic"/>
    </section>
  </xsl:template>

  <!-- Levels 2-3: heading is the id plus the text's (first) paragraph -->

  <xsl:template match="essential-understanding|topic">
    <section class="{local-name()}" id="{@xml:id}">
      <h2>
        <span class="id"><xsl:call-template name="display-id"/></span>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="text" mode="heading"/>
      </h2>
      <xsl:apply-templates select="text" mode="extra-blocks"/>
      <xsl:apply-templates select="learning-objective"/>
    </section>
  </xsl:template>

  <xsl:template match="learning-objective">
    <section class="learning-objective" id="{@xml:id}">
      <h3>
        <span class="id"><xsl:call-template name="display-id"/></span>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="text" mode="heading"/>
      </h3>
      <xsl:apply-templates select="text" mode="extra-blocks"/>
      <xsl:apply-templates select="essential-knowledge"/>
    </section>
  </xsl:template>

  <!-- Level 4: a paragraph rather than a heading, since EK text can be long -->

  <xsl:template match="essential-knowledge">
    <div class="essential-knowledge" id="{@xml:id}">
      <p>
        <span class="id"><xsl:call-template name="display-id"/></span>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="text" mode="heading"/>
      </p>
      <xsl:apply-templates select="text" mode="extra-blocks"/>
    </div>
  </xsl:template>

  <!-- CSA ids carry a level prefix (topic-1.1, lo-1.1.A, ek-1.1.A.1) to make
       them valid NCNames; strip it for display. CSP ids display as-is. -->

  <xsl:template name="display-id">
    <xsl:variable name="id" select="@xml:id"/>
    <xsl:choose>
      <xsl:when test="starts-with($id, 'topic-')">
        <xsl:value-of select="substring-after($id, 'topic-')"/>
      </xsl:when>
      <xsl:when test="starts-with($id, 'lo-')">
        <xsl:value-of select="substring-after($id, 'lo-')"/>
      </xsl:when>
      <xsl:when test="starts-with($id, 'ek-')">
        <xsl:value-of select="substring-after($id, 'ek-')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$id"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- A <text> is either inline content or a sequence of blocks whose first
       is a <p> (see build_ced_xml.py). The heading gets the inline content or
       first <p>; any remaining blocks render after the heading. -->

  <xsl:template match="text" mode="heading">
    <xsl:choose>
      <xsl:when test="p">
        <xsl:apply-templates select="p[1]/node()"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="text" mode="extra-blocks">
    <xsl:apply-templates select="*[position() &gt; 1]"/>
  </xsl:template>

  <!-- Blocks and inline markup: already HTML-shaped, so rebuild as-is -->

  <xsl:template match="p">
    <p><xsl:apply-templates/></p>
  </xsl:template>

  <xsl:template match="pre">
    <pre><xsl:apply-templates/></pre>
  </xsl:template>

  <xsl:template match="ul">
    <ul><xsl:apply-templates/></ul>
  </xsl:template>

  <xsl:template match="ol">
    <ol><xsl:copy-of select="@type"/><xsl:apply-templates/></ol>
  </xsl:template>

  <xsl:template match="li">
    <li><xsl:apply-templates/></li>
  </xsl:template>

  <xsl:template match="code">
    <code><xsl:apply-templates/></code>
  </xsl:template>

  <xsl:template match="em">
    <em><xsl:apply-templates/></em>
  </xsl:template>

</xsl:stylesheet>
