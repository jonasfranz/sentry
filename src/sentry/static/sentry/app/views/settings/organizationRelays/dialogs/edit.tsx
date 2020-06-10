import {t} from 'app/locale';

import FormStateManager from './dialogManager';

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
  onClose: () => void;
  relay: Relay;
};

class Edit extends FormStateManager<Props, FormStateManager['state']> {
  getDefaultState() {
    return {
      ...super.getDefaultState(),
      values: {
        name: this.props.relay.name,
        publicKey: this.props.relay.publicKey,
        description: this.props.relay.description || '',
      },
      disables: {publicKey: true},
      open: true,
    };
  }

  getTitle() {
    return t('Edit relay');
  }
}

export default Edit;
