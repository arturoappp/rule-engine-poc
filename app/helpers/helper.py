def entity_matches(entity1, entity2):
    if entity1 is None or entity2 is None:
        return False

    for key in entity1:
        if key in entity2 and entity1[key] != entity2[key]:
            return False

    for key in entity2:
        if key in entity1 and entity2[key] != entity1[key]:
            return False

    common_keys = set(entity1.keys()) & set(entity2.keys())
    return len(common_keys) > 0