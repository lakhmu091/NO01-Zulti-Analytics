# Reference only: based on the public example shown in Zulti's fairness documentation.
# Exact reproduction must confirm the draw-specific inputs and Erlang/OTP version.
server_seed = System.get_env("SERVER_SEED") || raise "Set SERVER_SEED"
ethereum_block_hash = System.get_env("ETH_BLOCK_HASH") || raise "Set ETH_BLOCK_HASH"
max_selectable_number = 45
selectable_numbers_count = 6

:rand.seed(:default, :erlang.phash2([server_seed, ethereum_block_hash]))

1..max_selectable_number
|> Enum.to_list()
|> Enum.shuffle()
|> Enum.take(selectable_numbers_count)
|> Enum.sort()
|> IO.inspect(label: "Reproduced draw (compare manually)")
