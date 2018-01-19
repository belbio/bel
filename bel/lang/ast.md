AST:
 {
    "subject": {
        "type": "Function",
        "span": [
            0,
            27
        ],
        "function": {
            "name": "proteinAbundance",
            "name_span": [
                0,
                15
            ],
            "parens_span": [
                16,
                27
            ]
        },
        "args": [
            {
                "arg": "HGNC:VEGFA",
                "type": "NSArg",
                "span": [
                    17,
                    26
                ],
                "nsarg": {
                    "ns": "HGNC",
                    "ns_val": "VEGFA",
                    "ns_span": [
                        17,
                        20
                    ],
                    "ns_val_span": [
                        22,
                        26
                    ]
                }
            }
        ]
    },
    "relation": {
        "name": "increases",
        "type": "Relation",
        "span": [
            29,
            37
        ]
    },
    "nested": {
        "subject": {
            "type": "Function",
            "span": [
                40,
                126
            ],
            "function": {
                "name": "compositeAbundance",
                "name_span": [
                    40,
                    57
                ],
                "parens_span": [
                    58,
                    126
                ]
            },
            "args": [
                {
                    "type": "Function",
                    "span": [
                        59,
                        86
                    ],
                    "function": {
                        "name": "proteinAbundance",
                        "name_span": [
                            59,
                            74
                        ],
                        "parens_span": [
                            75,
                            86
                        ]
                    },
                    "args": [
                        {
                            "arg": "HGNC:ITGB1",
                            "type": "NSArg",
                            "span": [
                                76,
                                85
                            ],
                            "nsarg": {
                                "ns": "HGNC",
                                "ns_val": "ITGB1",
                                "ns_span": [
                                    76,
                                    79
                                ],
                                "ns_val_span": [
                                    81,
                                    85
                                ]
                            }
                        }
                    ]
                },
                {
                    "type": "Function",
                    "span": [
                        89,
                        125
                    ],
                    "function": {
                        "name": "proteinAbundance",
                        "name_span": [
                            89,
                            104
                        ],
                        "parens_span": [
                            105,
                            125
                        ]
                    },
                    "args": [
                        {
                            "arg": "HGNC:PRKCA",
                            "type": "NSArg",
                            "span": [
                                106,
                                115
                            ],
                            "nsarg": {
                                "ns": "HGNC",
                                "ns_val": "PRKCA",
                                "ns_span": [
                                    106,
                                    109
                                ],
                                "ns_val_span": [
                                    111,
                                    115
                                ]
                            }
                        },
                        {
                            "type": "Function",
                            "span": [
                                118,
                                124
                            ],
                            "function": {
                                "name": "ma",
                                "name_span": [
                                    118,
                                    119
                                ],
                                "parens_span": [
                                    120,
                                    124
                                ]
                            },
                            "args": [
                                {
                                    "arg": "kin",
                                    "type": "StrArg",
                                    "span": [
                                        121,
                                        123
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "relation": {
            "name": "increases",
            "type": "Relation",
            "span": [
                39,
                182
            ]
        },
        "object": {
            "type": "Function",
            "span": [
                138,
                181
            ],
            "function": {
                "name": "biologicalProcess",
                "name_span": [
                    138,
                    154
                ],
                "parens_span": [
                    155,
                    181
                ]
            },
            "args": [
                {
                    "arg": "GO:\"cell-matrix adhesion\"",
                    "type": "NSArg",
                    "span": [
                        156,
                        180
                    ],
                    "nsarg": {
                        "ns": "GO",
                        "ns_val": "\"cell-matrix adhesion\"",
                        "ns_span": [
                            156,
                            157
                        ],
                        "ns_val_span": [
                            159,
                            180
                        ]
                    }
                }
            ]
        }
    }
}
