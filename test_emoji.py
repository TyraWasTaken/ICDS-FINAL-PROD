import emoji

# Test basic emoji conversion
print("Testing basic emoji conversion:")
print(emoji.emojize(":smiling_face:", language='alias'))
print(emoji.emojize(":red_heart:", language='alias'))
print(emoji.emojize(":thumbs_up:", language='alias'))

# Test with some emojis we use in our GUI
test_emojis = ["😊", "😂", "❤️", "👍", "🎉"]
print("\nTesting direct emoji display:")
for e in test_emojis:
    print(e, end=" ")

# Test emoji demojization (converting emoji to text)
print("\n\nTesting emoji to text conversion:")
for e in test_emojis:
    print(emoji.demojize(e, language='alias')) 