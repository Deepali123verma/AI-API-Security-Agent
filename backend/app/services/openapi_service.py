from app.utils.openapi_parser import OpenAPIParserError, ParsedOpenAPI, parse_spec_content


def parse_openapi_document(content: bytes) -> ParsedOpenAPI:
    try:
        return parse_spec_content(content)
    except OpenAPIParserError:
        raise
    except Exception as exc:
        raise OpenAPIParserError("Failed to parse OpenAPI specification") from exc
