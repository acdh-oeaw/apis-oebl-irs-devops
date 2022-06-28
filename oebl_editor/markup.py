"""Define the markup data structure of the editor as types

TODO: Add better types with frontend!

The data structure is generated from https://tiptap.dev/api/editor#get-json in the 
frontend and is a wrapper for the structure of 
https://prosemirror.net/docs/ref/#model.Document_Structure . 
Also there are some plugins, which extend the schema. Changes in the frontend should be reflected here. 
But since this is only a type hint, changes are, that at some point, this will get outdated. Hopefully not.

This is json data from a example document, which shows – the data structure is no yet build fully – will try to guess the missing data for now:

{
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
"""
from typing import List, TypedDict, Literal, Dict, Optional, Union

from tomlkit import datetime


class AbstractBaseNode(TypedDict):
    type: str
    attrs: Dict
    content: Optional[List['AbstractBaseNode']]


AnnotationTagName = Literal['annotation']
CommentTagName = Literal['comment']

MarkTagName = Union[AnnotationTagName, CommentTagName]

class AbstractMarkNode(AbstractBaseNode):
    type: MarkTagName

class AnnotationAttributes(TypedDict):
    """TODO: Define with front end"""
    entityId: Optional[str]

class AnnotationNode(AbstractMarkNode):
    type: AnnotationTagName
    attrs: AnnotationAttributes
    
    
class CommentAttributes(TypedDict):
    """TODO: Define with front end"""
    userID: int
    dateCreated: datetime
    dateModified: datetime
    text: str
    
class CommentNode(AbstractMarkNode):
    type: CommentTagName
    attrs: CommentAttributes
    
class AbstractMarkableBaseNode(AbstractBaseNode):
    marks: Optional[List[Union[AnnotationNode, CommentNode]]]


class ParagraphNode(AbstractMarkableBaseNode):
    type: Literal['paragraph']

class TextNode(AbstractMarkableBaseNode):
    type: Literal['text']
    text: str
    
class HeadingNode(TextNode):
    type: Literal['heading']

class EditorDocument(AbstractBaseNode):
    type: Literal['doc']    

    

    
    
    
    
    
        



