import {t} from 'app/locale';

import DialogManager from './dialogManager';

type Relay = {
  publicKey: string;
  name: string;
  created: string;
  firstUsed: string;
  lastUsed: string | null;
  lastModified?: string;
  description?: string;
};

type Props = {
  relay: Relay;
} & DialogManager['props'];

type State = DialogManager['state'];

class Edit extends DialogManager<Props, State> {
  getDefaultState() {
    return {
      ...super.getDefaultState(),
      values: {
        name: this.props.relay.name,
        publicKey: this.props.relay.publicKey,
        description: this.props.relay.description || '',
      },
      disables: {publicKey: true},
    };
  }

  getTitle() {
    return t('Edit relay');
  }
}

export default Edit;
