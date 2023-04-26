#!/bin/fish
# random httpie commands to mess around with

set -gx BASENAME localhost:5000

function sachet_init_db -d "initialize db"
	flask --debug --app sachet.server db drop --yes
	flask --debug --app sachet.server db create
	flask --debug --app sachet.server user create --username admin --admin yes --password password123
	flask --debug --app sachet.server user create --username user --admin no --password password123
end

function sachet_init_sess -d "initialize sessions in httpie"
	set TOKEN (http post $BASENAME/users/login username=user password=password123 | jq -r .auth_token)
	set ADMIN_TOKEN (http post $BASENAME/users/login username=admin password=password123 | jq -r .auth_token)
	http --session=sachet-admin get $BASENAME/users/user Authorization:"Bearer $ADMIN_TOKEN"
	http --session=sachet-user get $BASENAME/users/user Authorization:"Bearer $TOKEN"
end

function sachet_set_perms -d "setup permissions"
	http --session=sachet-admin patch $BASENAME/users/user permissions:='["READ", "CREATE", "LIST", "DELETE"]'
end

function sachet_upload -d "uploads a file"
	set URL (http --session=sachet-user post $BASENAME/files file_name="$argv" | jq -r .url)
	http --session=sachet-user -f post $BASENAME/$URL/content upload@$argv
end

function sachet_upload_meme -d "uploads a random meme"
	set MEME ~/med/memes/woof/(ls ~/med/memes/woof | shuf | head -n 1)
	upload $MEME
end

function sachet_list_files -d "lists files on a given page"
	argparse 'P/per-page=!_validate_int' -- $argv
	if not set -q _flag_per_page
		set _flag_per_page 5
	end
	http --session=sachet-user get localhost:5000/files per_page=$_flag_per_page page=$argv[1]
end

function sachet_download -d "downloads a given file id"
	http --session=sachet-user -f -d get $BASENAME/files/$argv/content
end

function sachet_delete -d "delete a given file id"
	http --session=sachet-user delete $BASENAME/files/$argv
end
