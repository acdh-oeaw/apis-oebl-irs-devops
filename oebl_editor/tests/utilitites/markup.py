from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from oebl_editor.markup import EditorDocument

def create_a_document(
      number_of_annotations: int = 1,
      comment_text: str = 'comment_text',
      additional_text: str = '',  
    ) -> 'EditorDocument':
    return {
  "type": "doc",
  "content": [
    {
      "type": "heading",
      "attrs": {},
      "content": [
        {
          "type": "text",
          "text": f"Überschrift 1 {additional_text}"
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
            for _ in range(number_of_annotations)
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
              "attrs": {
                  'text': comment_text,
              }
            }
          ],
          "text": "Kommentar"
        }
      ]
    },
  ]
}
    
    
class example_markup:
  get_original_version = staticmethod(create_a_document)
  get_changed_text = staticmethod(lambda: create_a_document(additional_text='Mehr Text'))
  get_changed_comment = staticmethod(lambda: create_a_document(comment_text='Zu viel Text!'))
  get_changed_annotations = staticmethod(lambda: create_a_document(number_of_annotations=2))
