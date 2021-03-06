# Copyright 2012-2013 (C) Daniel Watkins <daniel@daniel-watkins.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime

from docutils import nodes
from docutils.parsers.rst import directives
from git import Repo
from sphinx.util.compat import Directive


class GitChangelog(Directive):

    option_spec = {
        'revisions': directives.nonnegative_int,
        'rev-list': unicode,
        'detailed-message-pre': bool,
    }

    def run(self):
        if 'rev-list' in self.options and 'revisions' in self.options:
            self.state.document.reporter.warning(
                'Both rev-list and revisions options given; proceeding using'
                ' only rev-list.',
                line=self.lineno
            )
        commits = self._commits_to_display()
        markup = self._build_markup(commits)
        return markup

    def _commits_to_display(self):
        repo = self._find_repo()
        commits = self._filter_commits(repo)
        return commits

    def _get_env(self):
        return self.state.document.settings.env

    def _find_repo(self):
        env = self._get_env()
        repo = Repo(env.srcdir)
        return repo

    def _get_document_path(self):
        env = self._get_env()
        return env.doc2path(env.docname)

    def _filter_commits(self, repo):
        if 'rev-list' in self.options:
            return repo.iter_commits(rev=self.options['rev-list'])
        commits = repo.iter_commits(paths=self._get_document_path())
        revisions_to_display = self.options.get('revisions', 1)
        return list(commits)[:revisions_to_display]

    def _build_markup(self, commits):
        list_node = nodes.definition_list()
        for commit in commits:
            date_str = datetime.fromtimestamp(commit.authored_date)
            if '\n' in commit.message:
                message, detailed_message = commit.message.split('\n', 1)
            else:
                message = commit.message
                detailed_message = None

            item = nodes.list_item()
            item += [
                nodes.emphasis(text="Last Updated by "),
                nodes.strong(text=str(commit.author)),
                nodes.inline(text=" at "),
                nodes.emphasis(text=str(date_str)),
                nodes.inline(text=" with message "),
                nodes.strong(text=message),
            ]
            if detailed_message:
                detailed_message = detailed_message.strip()
                if self.options.get('detailed-message-pre', False):
                    item.append(
                        nodes.literal_block(text=detailed_message))
                else:
                    item.append(nodes.paragraph(text=detailed_message))
            list_node.append(item)
        return [list_node]


def setup(app):
    app.add_directive('git_changelog', GitChangelog)
