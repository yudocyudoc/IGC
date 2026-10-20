# Revisión de licencias F0

**Fecha:** 2026-10-20  
**Alcance:** dependencias fijadas, acciones GitHub, fuentes Modelica y grafos oficiales presentes en el SBOM F0; revisión documental de candidatos no incorporados.  
**Resultado:** revisión acotada completada. No es dictamen legal ni certifica el cumplimiento de la imagen completa del runner o contenedor.

## Criterio de lectura

Se registra la licencia declarada por la fuente oficial para la versión fijada. La presencia de una licencia en un proyecto upstream no convierte automáticamente el campo `licenseDeclared` de SPDX en una aserción verificada para cada archivo usado. Por eso el SBOM F0 conserva `NOASSERTION`. No se redistribuyen los archivos fuente de las ontologías ni las librerías Modelica en el artefacto de CI: se retienen hashes, metadatos y logs. La licencia de uso del motor OpenModelica no equivale a autorización para redistribuir la imagen ni cualquier binario generado.

## Dependencias Python fijadas

Las ocho versiones de `requirements-f0.lock.txt`:

| Paquete | Versión | Licencia declarada por la fuente de la versión fijada | Observación |
|---|---:|---|---|
| html5rdf | 1.2.1 | MIT | Conservar copyright y texto de licencia si se redistribuye. |
| owlrl | 7.6.2 | W3C Software and Document License 2015 | Conservar aviso íntegro, avisos preexistentes y aviso de cambios en redistribuciones. |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | Expresión alternativa reportada por PyPI; revisar metadatos/licencia del artefacto exacto antes de distribuir. |
| prettytable | 3.18.0 | BSD-3-Clause | Conservar avisos y disclaimer; no usar nombres para aval. |
| pyparsing | 3.3.3 | MIT | Conservar copyright y texto de licencia. |
| pySHACL | 0.40.1 | Apache-2.0 | Conservar licencia y NOTICE si lo incluye; marcar cambios y respetar aviso de patentes de Apache 2.0. |
| RDFLib | 7.6.0 | BSD-3-Clause | Conservar avisos y disclaimer; no usar nombres para aval. |
| wcwidth | 0.9.2 | MIT | Conservar copyright y texto de licencia. |

Fuentes de metadatos: [html5rdf](https://pypi.org/project/html5rdf/), [owlrl](https://pypi.org/project/owlrl/), [packaging 26.3](https://pypi.org/project/packaging/26.3/), [PrettyTable 3.18.0](https://pypi.org/project/prettytable/3.18.0/), [pyparsing 3.3.3](https://pypi.org/project/pyparsing/3.3.3/), [pySHACL 0.40.1](https://pypi.org/project/pyshacl/0.40.1/), [RDFLib 7.6.0](https://pypi.org/project/rdflib/7.6.0/), [wcwidth 0.9.2](https://pypi.org/project/wcwidth/0.9.2/). La [licencia W3C de 2015](https://www.w3.org/copyright/software-license-2015/) pide incluir el texto completo del aviso, avisos de propiedad intelectual preexistentes y un aviso de cambios en todas las copias o derivados.

## Acciones fijadas por commit

Las tres acciones inspeccionadas en los commits exactos declaran MIT: [actions/checkout](https://github.com/actions/checkout/blob/d23441a48e516b6c34aea4fa41551a30e30af803/LICENSE), [actions/setup-python](https://github.com/actions/setup-python/blob/5fda3b95a4ea91299a34e894583c3862153e4b97/LICENSE) y [actions/upload-artifact](https://github.com/actions/upload-artifact/blob/ea165f8d65b6e75b540449e92b4886f43607fa02/LICENSE). Si se redistribuye su código, se conserva el aviso MIT. Las dependencias JavaScript empaquetadas dentro de las acciones no están expandidas y permanecen fuera de esta revisión.

## Fuentes Modelica y OpenModelica

- **SystemDynamics 2.1.2**, commit `b986a2ea354ab550d627a392f857ad7c9997d961`: upstream declara BSD-3-Clause. Conservar aviso, condiciones y disclaimer en redistribuciones; no usar autores o nombres para aval. [README upstream](https://github.com/modelica-3rdparty/SystemDynamics/tree/b986a2ea354ab550d627a392f857ad7c9997d961).
- **Modelica Standard Library 4.0.0**, commit `6626538a236a34a390655b55d5e8c906bfe31772`: la fuente declara BSD-3-Clause. Aplican sus avisos y disclaimer; revisar además componentes de terceros señalados por el propio release antes de redistribuir un paquete completo. [Release v4.0.0](https://github.com/modelica/ModelicaStandardLibrary/releases/tag/v4.0.0) · [LICENSE en el commit fijado](https://github.com/modelica/ModelicaStandardLibrary/blob/6626538a236a34a390655b55d5e8c906bfe31772/LICENSE).
- **OpenModelica 1.27.1**, imagen oficial fijada por digest: los términos oficiales indican OSMC Public License o GNU AGPLv3 según el modo indicado en la distribución. No se inspeccionó el selector/aviso del modo de la imagen fijada ni el inventario completo de sus componentes. La ejecución actual usa la imagen en Actions; el repositorio no redistribuye la imagen. Antes de empaquetar OMC, runtimes, ejecutables enlazados o binarios generados, identificar el modo del artefacto concreto y revisar sus componentes/avisos. [Términos oficiales](https://openmodelica.org/terms-of-service/) · [licencia OSMC](https://openmodelica.org/free-and-open-source-software/full-license/).
- **BusinessSimulation 2.2.0** es candidato, no dependencia probada: upstream declara EUPL-1.2 o posterior. No se copió ni compiló; mantener fuera de la distribución hasta decidir adopción y revisar las condiciones de la versión exacta. [Release upstream](https://github.com/bslMS/BusinessSimulation/releases/tag/v2.2.0).

## Ontologías y estándares

- **CIDOC CRM 7.1.3**: el documento oficial de definición declara CC BY 4.0 y la serialización RDFS oficial contiene la misma declaración. Si se copia o transforma el material, atribuir fuente y licencia y señalar modificaciones. [Release oficial](https://cidoc-crm.org/Version/version-7.1.3) · [serialización RDFS](https://gitlab.isl.ics.forth.gr/cidoc-crm/cidoc_crm_rdf/-/blob/master/7.1.3/CIDOC_CRM_v7.1.3.rdf).
- **CRMinf 1.2.1**: el documento oficial de esa versión declara CC BY 4.0. Para la serialización RDF exacta del SBOM no se confirmó una declaración de licencia embebida; por ello el registro SPDX de ese grafo permanece `NOASSERTION`. [Documento de la versión](https://cidoc-crm.org/sites/default/files/CRMinf_v1.2.1%28stable%29.pdf) · [release oficial](https://cidoc-crm.org/crminf/ModelVersion/crminf-1.2.1).
- **CRMsci 3.2**: se revisaron la página oficial de la versión y sus declaraciones de clases/propiedades, pero no se pudo confirmar una licencia explícita aplicable a la serialización RDF fijada. Se conserva `NOASSERTION` hasta obtener una declaración primaria para ese archivo. [Release oficial](https://cidoc-crm.org/crmsci/fm_releases) · [declaraciones de v3.2](https://cidoc-crm.org/extensions/crmsci/html/CRMsci_v3.2.html).
- **PROV-O (2013-04-30)**: el grafo procede de W3C. Para reutilizar material W3C aplican los avisos y términos indicados por el propio recurso; la licencia W3C Software and Document License 2015 exige conservar aviso completo, avisos preexistentes y cambios en copias/derivados. [PROV-O](https://www.w3.org/TR/prov-o/) · [licencia W3C 2015](https://www.w3.org/copyright/software-license-2015/). El snapshot de CI registra hash, no redistribuye el grafo.

La atribución CC BY requiere crédito apropiado, enlace a la licencia e indicación de modificaciones; no sugiere respaldo del titular. [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

## Licencias de componentes de plataforma: sin cierre

El SBOM SPDX 2.3 contiene 1,451 registros. Se revisó la licencia declarada de los ocho paquetes Python directos/transitivos, tres acciones, fuentes Modelica y fuentes ontológicas arriba listadas. Los 1,210 paquetes dpkg del runner y 222 del contenedor OpenModelica no se auditaron uno por uno contra su copyright/metadatos de distribución; herramientas del runner instaladas fuera de dpkg y dependencias internas de Actions también quedan fuera. Por tanto:

- Los campos SPDX siguen en `NOASSERTION`; no se afirma que los 1,451 registros estén autorizados para redistribución.
- La declaración oficial de una documentación o upstream no sustituye la identificación legal de cada archivo redistribuible.
- Antes de distribuir una imagen, binarios, bibliotecas, artefactos construidos o una copia del grafo RDF, obtener el manifiesto legal por componente y ensamblar los avisos/licencias exigidos.
- El uso actual de las dependencias en una ejecución de CI no se presenta como redistribución de esos componentes dentro del producto IGC.

## Cierre F0

**Revisión documental acotada: COMPLETADA.**  
**Cierre de licencias de plataforma/redistribución integral: PENDIENTE.**  
**Estado de SBOM: NOASSERTION; `licenses_verified: false`.**

Esta revisión registra fuentes y límites para el desarrollo; no es asesoría legal ni una aprobación de distribución.
