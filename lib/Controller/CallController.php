<?php
namespace OCA\SipCall\Controller;

use OCP\AppFramework\Controller;
use OCP\IRequest;
use OCP\AppFramework\Http\JSONResponse;

class CallController extends Controller {

    public function __construct($AppName, IRequest $request) {
        parent::__construct($AppName, $request);
    }

    /**
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    public function index(): JSONResponse {
        return new JSONResponse(['status' => 'ok']);
    }

    /**
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    public function start(): JSONResponse {
        // TODO: integrate with FastAPI backend
        return new JSONResponse(['message' => 'Call initiated']);
    }
}
