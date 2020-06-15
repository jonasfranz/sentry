import React from 'react';
import {RouteComponentProps} from 'react-router/lib/Router';
import styled from '@emotion/styled';

import {openModal} from 'app/actionCreators/modal';
import {Panel, PanelBody, PanelHeader, PanelAlert} from 'app/components/panels';
import {t, tct} from 'app/locale';
import AsyncComponent from 'app/components/asyncComponent';
import SettingsPageHeader from 'app/views/settings/components/settingsPageHeader';
import {Organization} from 'app/types';
import ExternalLink from 'app/components/links/externalLink';
import space from 'app/styles/space';
import Button from 'app/components/button';
import {addErrorMessage, addSuccessMessage} from 'app/actionCreators/indicator';

import {Relay} from './types';
import Content from './content';
import {Add, Edit} from './dialogs';

const RELAY_DOCS_LINK = 'https://getsentry.github.io/relay/';

type Props = {
  organization: Organization;
} & RouteComponentProps<{orgId: string}, {}>;

type State = AsyncComponent['state'] & {
  relays: Array<Relay>;
  openAddDialog: boolean;
  editRelay?: Relay;
};

class Relays extends AsyncComponent<Props, State> {
  getEndpoints(): ReturnType<AsyncComponent['getEndpoints']> {
    return [['relays', `/organizations/${this.props.organization.slug}/relay-keys/`]];
  }

  handleDelete = (publicKey: Relay['publicKey']) => async () => {
    try {
      await this.api.requestPromise(
        `/organizations/${this.props.organization.slug}/relay-keys/${publicKey}/`,
        {method: 'DELETE'}
      );
      addSuccessMessage('Successfully deleted relay public key');
      this.setState(prevState => ({
        relays: prevState.relays.filter(relay => relay.publicKey !== publicKey),
      }));
    } catch {
      addErrorMessage('An unknown error occurred while deleting relay public key');
    }
  };

  handleSave = async (data: Parameters<Add['props']['onSave']>[0]) => {
    try {
      const response = await this.api.requestPromise(
        `/organizations/${this.props.organization.slug}/relay-keys/${data.publicKey}/`,
        {method: 'PUT', data}
      );
      addSuccessMessage('Successfully saved relay public key');
      this.setState(prevState => ({
        relays: [...prevState.relays, response],
      }));
    } catch {
      addErrorMessage('An unknown error occurred while saving relay public key');
    }
  };

  handleToggleEditDialog = (publicKey?: Relay['publicKey']) => () => {
    const editRelay = this.state.relays.find(relay => relay.publicKey === publicKey);

    if (!editRelay) {
      return;
    }

    openModal(modalProps => <Edit {...modalProps} relay={editRelay} />);
  };

  handleToggleAddDialog = () => {
    openModal(modalProps => <Add {...modalProps} onSave={this.handleSave} />);
  };

  renderBody() {
    const {relays} = this.state;

    return (
      <React.Fragment>
        <SettingsPageHeader title={t('Relays')} />
        <Panel>
          <PanelHeader>{t('Relays')}</PanelHeader>
          <PanelAlert type="info">
            {tct('For more details, see [linkToDocs].', {
              linkToDocs: (
                <ExternalLink href={RELAY_DOCS_LINK}>
                  {t('full Relay documentation')}
                </ExternalLink>
              ),
            })}
          </PanelAlert>
          <PanelBody>
            <Content
              relays={relays}
              onEdit={this.handleToggleEditDialog}
              onDelete={this.handleDelete}
            />
          </PanelBody>
          <PanelAction>
            <Button href={RELAY_DOCS_LINK} target="_blank">
              {t('Read the docs')}
            </Button>
            <Button onClick={this.handleToggleAddDialog} priority="primary">
              {t('Add Relay')}
            </Button>
          </PanelAction>
        </Panel>
      </React.Fragment>
    );
  }
}

export default Relays;

const PanelAction = styled('div')`
  padding: ${space(1)} ${space(2)};
  display: grid;
  grid-gap: ${space(1)};
  grid-template-columns: auto auto;
  justify-content: flex-end;
  border-top: 1px solid ${p => p.theme.borderDark};
`;
