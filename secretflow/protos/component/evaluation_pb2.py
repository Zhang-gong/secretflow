# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: secretflow/protos/component/evaluation.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from secretflow.protos.component import comp_pb2 as secretflow_dot_protos_dot_component_dot_comp__pb2
from secretflow.protos.component import data_pb2 as secretflow_dot_protos_dot_component_dot_data__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='secretflow/protos/component/evaluation.proto',
  package='secretflow.component',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n,secretflow/protos/component/evaluation.proto\x12\x14secretflow.component\x1a&secretflow/protos/component/comp.proto\x1a&secretflow/protos/component/data.proto\"\xc7\x01\n\rNodeEvalParam\x12\x0e\n\x06\x64omain\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0f\n\x07version\x18\x03 \x01(\t\x12\x12\n\nattr_paths\x18\x04 \x03(\t\x12.\n\x05\x61ttrs\x18\x05 \x03(\x0b\x32\x1f.secretflow.component.Attribute\x12.\n\x06inputs\x18\x06 \x03(\x0b\x32\x1e.secretflow.component.DistData\x12\x13\n\x0boutput_uris\x18\x07 \x03(\t\"A\n\x0eNodeEvalResult\x12/\n\x07outputs\x18\x01 \x03(\x0b\x32\x1e.secretflow.component.DistDatab\x06proto3'
  ,
  dependencies=[secretflow_dot_protos_dot_component_dot_comp__pb2.DESCRIPTOR,secretflow_dot_protos_dot_component_dot_data__pb2.DESCRIPTOR,])




_NODEEVALPARAM = _descriptor.Descriptor(
  name='NodeEvalParam',
  full_name='secretflow.component.NodeEvalParam',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='domain', full_name='secretflow.component.NodeEvalParam.domain', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='name', full_name='secretflow.component.NodeEvalParam.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='version', full_name='secretflow.component.NodeEvalParam.version', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='attr_paths', full_name='secretflow.component.NodeEvalParam.attr_paths', index=3,
      number=4, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='attrs', full_name='secretflow.component.NodeEvalParam.attrs', index=4,
      number=5, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='inputs', full_name='secretflow.component.NodeEvalParam.inputs', index=5,
      number=6, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='output_uris', full_name='secretflow.component.NodeEvalParam.output_uris', index=6,
      number=7, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=151,
  serialized_end=350,
)


_NODEEVALRESULT = _descriptor.Descriptor(
  name='NodeEvalResult',
  full_name='secretflow.component.NodeEvalResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='outputs', full_name='secretflow.component.NodeEvalResult.outputs', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=352,
  serialized_end=417,
)

_NODEEVALPARAM.fields_by_name['attrs'].message_type = secretflow_dot_protos_dot_component_dot_comp__pb2._ATTRIBUTE
_NODEEVALPARAM.fields_by_name['inputs'].message_type = secretflow_dot_protos_dot_component_dot_data__pb2._DISTDATA
_NODEEVALRESULT.fields_by_name['outputs'].message_type = secretflow_dot_protos_dot_component_dot_data__pb2._DISTDATA
DESCRIPTOR.message_types_by_name['NodeEvalParam'] = _NODEEVALPARAM
DESCRIPTOR.message_types_by_name['NodeEvalResult'] = _NODEEVALRESULT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

NodeEvalParam = _reflection.GeneratedProtocolMessageType('NodeEvalParam', (_message.Message,), {
  'DESCRIPTOR' : _NODEEVALPARAM,
  '__module__' : 'secretflow.protos.component.evaluation_pb2'
  # @@protoc_insertion_point(class_scope:secretflow.component.NodeEvalParam)
  })
_sym_db.RegisterMessage(NodeEvalParam)

NodeEvalResult = _reflection.GeneratedProtocolMessageType('NodeEvalResult', (_message.Message,), {
  'DESCRIPTOR' : _NODEEVALRESULT,
  '__module__' : 'secretflow.protos.component.evaluation_pb2'
  # @@protoc_insertion_point(class_scope:secretflow.component.NodeEvalResult)
  })
_sym_db.RegisterMessage(NodeEvalResult)


# @@protoc_insertion_point(module_scope)
