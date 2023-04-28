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

function sachet_anon -d "setup anonymous user's permissions"
	if test -z $argv
		set argv '["READ", "CREATE", "LIST", "DELETE"]'
	end
	http --session=sachet-admin patch $BASENAME/admin/settings default_permissions:=$argv
end

function sachet_upload -d "uploads a file"
	argparse 's/session=?' -- $argv
	set FNAME (basename $argv)
	set URL (http --session=$_flag_session post $BASENAME/files file_name=$FNAME | jq -r .url)
	http --session=$_flag_session -f post $BASENAME/$URL/content upload@$argv
end

function sachet_upload_meme -d "uploads a random meme"
	set MEME ~/med/memes/woof/(ls ~/med/memes/woof | shuf | head -n 1)
	sachet_upload $MEME
end

function sachet_list -d "lists files on a given page"
	argparse 'P/per-page=!_validate_int' 's/session=?' -- $argv
	if not set -q _flag_per_page
		set _flag_per_page 5
	end
	http --session=$_flag_session get localhost:5000/files per_page=$_flag_per_page page=$argv[1]
end

function sachet_download -d "downloads a given file id"
	argparse 's/session=?' -- $argv
	http --session=$_flag_session -f -d get $BASENAME/files/$argv/content
end

function sachet_delete -d "delete given file ids"
	argparse 's/session=?' -- $argv
	for file in $argv
		http --session=$_flag_session delete $BASENAME/files/$file
	end
end
