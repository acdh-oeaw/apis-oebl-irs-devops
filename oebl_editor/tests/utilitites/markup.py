from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from oebl_editor.markup import EditorDocument

def create_a_document() -> 'EditorDocument':
    return {
  "type": "doc",
  "content": [
    {
      "type": "heading",
      "attrs": {},
      "content": [
        {
          "type": "text",
          "text": "Überschrift 1"
        }
      ]
    },
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Text mit "
        },
        {
          "type": "text",
          "marks": [
            {
              "type": "annotation",
              "attrs": {}
            }
          ],
          "text": "Annotation"
        }
      ]
    },
    {
      "type": "heading",
      "attrs": {},
      "content": [
        {
          "type": "text",
          "text": "Überschrift 2"
        }
      ]
    },
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Text mit "
        },
        {
          "type": "text",
          "marks": [
            {
              "type": "comment",
              "attrs": {}
            }
          ],
          "text": "Kommentar"
        }
      ]
    },
  ]
}