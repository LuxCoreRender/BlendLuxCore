
def assertListsAlmostEqual(test_case, list1, list2):
    test_case.assertEqual(len(list1), len(list2))

    for i in range(len(list1)):
        test_case.assertAlmostEqual(list1[i], list2[i])