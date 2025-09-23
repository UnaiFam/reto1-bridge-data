# DESAFIO 

En la fase final del Bootcamp se nos encarga un desafio que debemos realizar junto con las demas clases del bootcamp; ciberseguridad, marketing,fullstack. 

## Problema especifico:

Dentro del desafio se hace necesario el reconocimiento de los tickets, ello se puede hacer mediante un programa OCR, no obstante, en los ultimos años han surgido soluciones que nos permiten realizar este mismo trabajo de forma mas rapida. dado el caracter de sprint del desafio se hace necesario el uso de herramientas de IA. 

En concreto, para este punto se utilizará el llamcloud.IA. [LlamaCloud](https://cloud.llamaindex.a)

## Datos que vamos a encontrar en todas las facturas:

Segu la Web de la hacienda tributaria son obligatorias las siguientes:
"Las facturas simplificadas deben contener al menos los siguientes datos:

- Número y, en su caso, serie. La numeración será correlativa.

- Fecha de expedición.

- Fecha en que se hayan efectuado las operaciones o se haya recibido el pago anticipado, siempre que sea distinta a la de expedición de la factura.

- Número de identificación fiscal, así como el nombre y apellidos, razón o denominación social del obligado a su expedición.

-  identificación del tipo de bienes entregados o de servicios prestados.

- Tipo impositivo aplicado y, opcionalmente también la expresión «IVA incluido».

- Contraprestación total.

-  el caso de facturas rectificativas, la referencia expresa e inequívoca de la factura rectificada y de las especificaciones que se modifican.

- Las menciones recogidas en las facturas ordinarias relativas a la aplicación de regímenes especiales y a determinadas operaciones (exentas, con inversión del sujeto pasivo, etc.)."

No obstante, no todo lo que aqui aparece se debe de recoger con el OCR.
Recogeremos:
- Nombre de la empresa. 
- NIF
- Fecha de expedición.
- Bienes ofertados.
- contraprestacion total.
- Lugar(asumiremos que en la factura esta el local donde se ha expedido) 

En este caso asumiremos que las facturas vienen con la dirección de establecimiento. 

CONTRASEÑA 1: llx-80200pQgQeS1QWleqJHsDUjIBFf4QCbQIOyqyPJbo6KnGNRq
nombre: LEER FACTURAS 1
id: 882591e8-1c77-4ae7-a494-77ce1a30d4ce

# Tipos de archivos que soporta 
LlamaExtract supports the following file formats:

Documents: PDF (.pdf), Word (.docx)
Text files: Plain text (.txt), CSV (.csv), JSON (.json), HTML (.html, .htm), Markdown (.md)
Images: PNG (.png), JPEG (.jpg, .jpeg)


schema: {
  "additionalProperties": false,
  "properties": {
    "FACTURA": {
      "description": "Invoice number, usually a unique identifier for the invoice.",
      "type": "string"
    },
    "NIF": {
      "description": "NUMERO QUE IDENTIFICA A LA EMPRESA SUELE ESTAR PRECEDIDO DE LA PALABRA NIF O CIF, SUELE EMPEZAR POR UNA LETRA SEGUIDO DE 8 NUMEROS",
      "type": "string"
    },
    "EMPRESA": {
      "description": "Name of the entity issuing the invoice.",
      "type": "string"
    },
    "DIRECCIÓN": {
      "description": "Full address of the invoice issuer, including street, city, region, and country.",
      "type": "string"
    },
    "iva_percentage": {
      "description": "IVA percentage applied to the invoice (e.g., 21).",
      "type": "number"
    },
    "products": {
      "description": "Array of products listed in the invoice.",
      "items": {
        "additionalProperties": false,
        "properties": {
          "product_name": {
            "description": "Name or description of the product.",
            "type": "string"
          },
          "units": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Number of units of the product."
          },
          "unit_price": {
            "description": "Price per unit of the product, including currency symbol (e.g., 150€).",
            "type": "string"
          },
          "total_price": {
            "description": "Total price for the product (units * unit_price), including currency symbol (e.g., 150€).",
            "type": "string"
          }
        },
        "required": [
          "product_name",
          "units",
          "unit_price",
          "total_price"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "iva_amount": {
      "description": "Amount of IVA charged, including currency symbol (e.g., 31,5€).",
      "type": "string"
    },
    "total_amount": {
      "description": "Total amount of the invoice, including IVA, including currency symbol (e.g., 181,5€).",
      "type": "string"
    }
  },
  "required": [
    "FACTURA",
    "NIF",
    "EMPRESA",
    "DIRECCIÓN",
    "iva_percentage",
    "products",
    "iva_amount",
    "total_amount"
  ],
  "type": "object"
}




# 