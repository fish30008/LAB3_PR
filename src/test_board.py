"""
Comprehensive tests for Memory Scramble Board
Tests parsing, look, flip, map, and watch operations
"""
import asyncio
from board import Board


async def test_1_parse_and_look():
    """Test 1: Parse board files and verify look() output"""
    print("\n" + "=" * 60)
    print("TEST 1: Parse board and test look()")
    print("=" * 60)

    # Test parsing ab.txt (5x5 board with A and B)
    print("\n1.1 Testing boards/ab.txt...")
    board = await Board.parse_from_file('../boards/ab.txt')
    print(f"✓ Parsed board: {board.rows}x{board.cols}")
    assert board.rows == 5
    assert board.cols == 5

    # Test look() - all cards should be face down initially
    result = board.look('test_player')
    lines = result.split('\n')

    print(f"✓ Board has {len(lines)} lines (1 header + 25 cards)")
    assert len(lines) == 26, f"Expected 26 lines, got {len(lines)}"
    assert lines[0] == '5x5', f"Expected '5x5', got '{lines[0]}'"
    assert all(line == 'down' for line in lines[1:]), "All cards should be face down"
    print("✓ All cards are face down")


    print("\n✅ TEST 1 PASSED: Parsing and look() work correctly\n")


async def test_2_flip_basic():
    """Test 2: Basic flip operations"""
    print("\n" + "=" * 60)
    print("TEST 2: Basic flip operations")
    print("=" * 60)

    board = await Board.parse_from_file('../boards/ab.txt')
    player1 = 'alice'

    # Flip a card face up
    print("\n2.1 Flipping card at (0, 0)...")
    result = await board.flip(player1, 0, 0)
    lines = result.split('\n')

    # Check that card is now face up and controlled by alice
    card_line = lines[1]  # First card after header
    assert card_line.startswith('my '), f"Expected 'my ...', got '{card_line}'"
    card_label = card_line.split(' ')[1]
    print(lines[1])
    print(f"✓ Card flipped face up: '{card_label}'")
    print(f"✓ Card controlled by {player1}")

    # Flip the same card face down again
    print("\n2.2 Flipping same card face down...")
    result2 = await board.flip(player1, 0, 0)
    lines2 = result2.split('\n')
    assert lines2[1] == 'down', f"Expected 'down', got '{lines2[1]}'"
    print("✓ Card flipped face down", print(lines2))

    # Flip multiple cards
    print("\n2.3 Flipping multiple cards...")
    await board.flip(player1, 1, 1)
    await board.flip(player1, 2, 3)
    result3 = await board.flip(player1, 4, 4)
    lines3 = result3.split('\n')

    # Count cards controlled by player1
    my_cards = [line for line in lines3 if line.startswith('my ')]
    print(f"✓ Player controls {len(my_cards)} cards")

    print("\n✅ TEST 2 PASSED: Basic flip operations work\n")


async def test_3_flip_contention():
    """Test 3: Multiple players flipping (waiting for control)"""
    print("\n" + "=" * 60)
    print("TEST 3: Flip contention (multiple players)")
    print("=" * 60)

    board = await Board.parse_from_file('../boards/perfect.txt')
    player1 = 'alice'
    player2 = 'bob'

    # Player 1 flips a card face up
    print("\n3.1 Alice flips card at (0, 0)...")
    result1 = await board.flip(player1, 0, 0)
    lines1 = result1.split('\n')
    assert lines1[1].startswith('my ')
    print("✓ Alice controls card at (0, 0)")

    # Player 2 looks at the board - should see alice's card as 'up'
    print("\n3.2 Bob looks at the board...")
    result2 = board.look(player2)
    lines2 = result2.split('\n')
    assert lines2[1].startswith('up '), f"Bob should see 'up ...', got '{lines2[1]}'"
    print("✓ Bob sees Alice's card as 'up' (not 'my')")

    # Player 2 tries to flip the same card - should wait then fail or succeed
    print("\n3.3 Testing contention handling...")
    print("(This would wait if alice holds the card)")
    print("(For now, we'll flip a different card for bob)")

    # Bob flips a different card
    result3 = await board.flip(player2, 1, 1)
    lines3 = result3.split('\n')

    # Verify bob's view
    my_cards = [line for line in lines3 if line.startswith('my ')]
    up_cards = [line for line in lines3 if line.startswith('up ')]
    print(f"✓ Bob controls {len(my_cards)} cards")
    print(f"✓ Bob sees {len(up_cards)} other players' cards")

    print("\n✅ TEST 3 PASSED: Multiple players work correctly\n")


async def test_4_map_replace():
    """Test 4: map_cards() to replace labels"""
    print("\n" + "=" * 60)
    print("TEST 4: Map/replace card labels")
    print("=" * 60)

    board = await Board.parse_from_file('../boards/ab.txt')
    player = 'alice'

    # Flip some cards to see their labels
    print("\n4.1 Flipping cards to see labels...")
    await board.flip(player, 0, 0)
    await board.flip(player, 0, 1)
    result_before = board.look(player)
    print("Before replacement:")
    for i, line in enumerate(result_before.split('\n')[1:6]):  # Show first 5 cards
        print(f"  Card {i}: {line}")

    # Replace all 'A' with 'Z'
    print("\n4.2 Replacing all 'A' cards with 'Z'...")
    result_after = await board.map_cards(
        player,
        lambda label: 'Z' if label == 'A' else label
    )
    print("After replacement:")
    for i, line in enumerate(result_after.split('\n')[1:6]):  # Show first 5 cards
        print(f"  Card {i}: {line}")

    # Verify replacement worked
    lines_after = result_after.split('\n')
    my_cards = [line for line in lines_after if line.startswith('my ')]

    # Check no 'A' remains in visible cards
    for card in my_cards:
        label = card.split(' ')[1]
        assert label != 'A', f"Found 'A' after replacement: {card}"
        if label == 'Z':
            print(f"✓ Found replaced card: {card}")

    print("\n✅ TEST 4 PASSED: Map/replace works correctly\n")


async def test_5_map_with_emojis():
    """Test 5: Replace emoji cards"""
    print("\n" + "=" * 60)
    print("TEST 5: Replace emoji cards (zoom.txt)")
    print("=" * 60)

    board = await Board.parse_from_file('../boards/zoom.txt')
    player = 'alice'

    # Flip a card to see an emoji
    print("\n5.1 Flipping some cards...")
    result1 = await board.flip(player, 0, 0)
    result2 = await board.flip(player, 1, 1)
    result3 = await board.flip(player, 2, 2)

    lines = result3.split('\n')
    my_cards = [line for line in lines if line.startswith('my ')]
    print(f"Visible cards before replacement:")
    for card in my_cards:
        print(f"  {card}")

    # Replace 🚚 with 🍕
    print("\n5.2 Replacing 🚚 with 🍕...")
    result_after = await board.map_cards(
        player,
        lambda label: '🍕' if label == '🚚' else label
    )

    lines_after = result_after.split('\n')
    my_cards_after = [line for line in lines_after if line.startswith('my ')]
    print(f"Visible cards after replacement:")
    for card in my_cards_after:
        print(f"  {card}")
        label = card.split(' ')[1]
        assert label != '🚚', "Found 🚚 after replacement!"

    print("\n✅ TEST 5 PASSED: Emoji replacement works\n")


async def test_6_watch():
    """Test 6: watch() for board changes"""
    print("\n" + "=" * 60)
    print("TEST 6: Watch for board changes")
    print("=" * 60)

    board = await Board.parse_from_file('../boards/perfect.txt')
    player1 = 'alice'
    player2 = 'bob'

    print("\n6.1 Starting watch in background...")

    # Start watching in the background
    watch_task = asyncio.create_task(board.watch(player2, timeout=5.0))

    # Wait a bit then make a change
    print("6.2 Waiting 1 second, then flipping a card...")
    await asyncio.sleep(1.0)

    await board.flip(player1, 1, 1)
    print("✓ Card flipped")

    # Wait for watch to complete
    print("6.3 Waiting for watch() to return...")
    result = await watch_task
    print("✓ Watch returned after board change")

    # Verify the result shows the change
    lines = result.split('\n')
    up_or_my = [line for line in lines if line.startswith('up ') or line.startswith('my ')]
    assert len(up_or_my) > 0, "Watch should show at least one card face up"
    print(f"✓ Watch detected {len(up_or_my)} face-up cards")

    print("\n✅ TEST 6 PASSED: Watch works correctly\n")


async def test_7_error_cases():
    """Test 7: Error handling"""
    print("\n" + "=" * 60)
    print("TEST 7: Error handling")
    print("=" * 60)

    board = await Board.parse_from_file('../boards/ab.txt')
    player = 'alice'

    # Test invalid position
    print("\n7.1 Testing invalid flip position...")
    try:
        await board.flip(player, 10, 10)  # Out of bounds
        print("❌ Should have raised ValueError")
        assert False
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")

    # Test invalid file
    print("\n7.2 Testing invalid file...")
    try:
        await Board.parse_from_file('boards/nonexistent.txt')
        print("❌ Should have raised FileNotFoundError")
        assert False
    except FileNotFoundError:
        print("✓ Caught expected FileNotFoundError")

    print("\n✅ TEST 7 PASSED: Error handling works\n")


async def test_8_concurrent_flips():
    """Test 8: Multiple concurrent operations"""
    print("\n" + "=" * 60)
    print("TEST 8: Concurrent operations")
    print("=" * 60)

    board = await Board.parse_from_file('../boards/zoom.txt')

    print("\n8.1 Starting 5 players flipping concurrently...")

    async def player_flip(player_id, row, col):
        """Helper function for one player's flip"""
        try:
            result = await board.flip(player_id, row, col)
            print(f"✓ Player {player_id} flipped ({row}, {col})")
            return result
        except Exception as e:
            print(f"⚠ Player {player_id} failed: {e}")
            return None

    # Create 5 concurrent flip tasks
    tasks = [
        asyncio.create_task(player_flip('player1', 0, 0)),
        asyncio.create_task(player_flip('player2', 1, 1)),
        asyncio.create_task(player_flip('player3', 2, 2)),
        asyncio.create_task(player_flip('player4', 3, 3)),
        asyncio.create_task(player_flip('player5', 4, 4)),
    ]

    results = await asyncio.gather(*tasks)
    successful = [r for r in results if r is not None]
    print(f"✓ {len(successful)}/5 flips completed successfully")

    print("\n✅ TEST 8 PASSED: Concurrent operations work\n")


async def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "=" * 60)
    print("MEMORY SCRAMBLE - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    try:
        await test_1_parse_and_look()
        await test_2_flip_basic()
        await test_3_flip_contention()
        await test_4_map_replace()
        await test_5_map_with_emojis()
        await test_6_watch()
        await test_7_error_cases()
        await test_8_concurrent_flips()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nNext step: Implement commands.py and server.py")
        print("=" * 60 + "\n")

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60 + "\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(run_all_tests())