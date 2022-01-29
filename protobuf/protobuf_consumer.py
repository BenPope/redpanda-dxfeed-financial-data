#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 Confluent Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# This is a simple example of the SerializingProducer using protobuf.
#
# To regenerate Protobuf classes you must first install the protobuf
# compiler. Once installed you may call protoc directly or use make.
#
# See the protocol buffer docs for instructions on installing and using protoc.
# https://developers.google.com/protocol-buffers/docs/pythontutorial
#
# After installing protoc execute the following command from the examples
# directory to regenerate the user_pb2 module.
# `make`
#
import argparse
import time

# Protobuf generated class; resides at ./user_pb2.py
import user_pb2
from confluent_kafka import DeserializingConsumer
from confluent_kafka.error import ConsumeError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.protobuf import ProtobufDeserializer
from confluent_kafka.serialization import StringDeserializer


def main(args):
    topic = args.topic
    subject = f"{topic}-value"

    protobuf_deserializer = ProtobufDeserializer(user_pb2.User)
    string_deserializer = StringDeserializer('utf_8')

    consumer_conf = {'bootstrap.servers': args.bootstrap_servers,
                     'key.deserializer': string_deserializer,
                     'value.deserializer': protobuf_deserializer,
                     'group.id': args.group,
                     'auto.offset.reset': "earliest"}

    consumer = None
    schema_registry_conf = {'url': args.schema_registry}

    for i in range(60):
        try:
            schema_registry_client = SchemaRegistryClient(schema_registry_conf)
            subs = schema_registry_client.get_subjects()
            if subject in subs:
                consumer = DeserializingConsumer(consumer_conf)
                consumer.subscribe([topic])
                break
            else:
                print(
                    f"Failed to get subject: {subject}, retrying", flush=True)
                time.sleep(1)
        except Exception as e:
            print(f"Failed to connect: {e}, retrying", flush=True)
            time.sleep(1)

    while consumer:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            user = msg.value()
            if user is not None:
                print("User record {}:\n"
                      "\tname: {}\n"
                      "\tfavorite_number: {}\n"
                      "\tfavorite_color: {}\n"
                      .format(msg.key(), user.name,
                              user.favorite_color,
                              user.favorite_number))
        except KeyboardInterrupt:
            break
        except ConsumeError as e:
            print(f"Error consuming, retrying {e}")
            time.sleep(1)

    consumer.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="DeserializingConsumer Example")
    parser.add_argument('-b', dest="bootstrap_servers", required=True,
                        help="Bootstrap broker(s) (host[:port])")
    parser.add_argument('-s', dest="schema_registry", required=True,
                        help="Schema Registry (http(s)://host[:port]")
    parser.add_argument('-t', dest="topic", default="example_serde_protobuf",
                        help="Topic name")
    parser.add_argument('-g', dest="group", default="example_serde_protobuf",
                        help="Consumer group")

    main(parser.parse_args())
